import hashlib
import json
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import Answer, Assessment, AssessmentAttempt
from app.models.content import ContentVersion, DeviceContent
from app.models.identity import Device
from app.models.learning import LearningEvent, LessonProgress, StudentNote
from app.models.sync import DeviceSyncState, ServerChangeLog, SyncEventInbox
from app.modules.sync.schemas import (
    ChangeItem,
    SyncBatchRequest,
    SyncBatchResponse,
    SyncChangesResponse,
    SyncStatusResponse,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def ingest_event_batch(
    db: Session, school_id: str, caller_user_id: str, req: SyncBatchRequest
) -> SyncBatchResponse:
    # Verify device exists and not revoked
    device = db.execute(
        select(Device).where(Device.id == req.device_id)
    ).scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="UNAUTHENTICATED: Originating device is not registered",
        )
    if device.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_REVOKED: This device has been revoked and cannot submit sync events",
        )
    if device.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PERMISSION_DENIED: Device does not belong to this school",
        )

    acknowledged: list[str] = []
    duplicates: list[str] = []
    rejected: list[str] = []
    now = datetime.now(UTC)
    max_sequence = 0
    seen_in_batch = set()

    for ev in req.events:
        # Validate event ownership and boundaries
        if (
            ev.device_id != req.device_id
            or ev.school_id != school_id
            or ev.user_id != caller_user_id
        ):
            rejected.append(ev.event_id)
            continue

        # Check in-batch duplicate
        if ev.event_id in seen_in_batch:
            duplicates.append(ev.event_id)
            continue
        seen_in_batch.add(ev.event_id)

        # Check idempotency: unique constraint on (school_id, event_id)
        existing_inbox = db.execute(
            select(SyncEventInbox).where(
                SyncEventInbox.school_id == ev.school_id,
                SyncEventInbox.event_id == ev.event_id,
            )
        ).scalar_one_or_none()

        if existing_inbox:
            duplicates.append(ev.event_id)
            continue

        # Compute payload hash
        payload_str = json.dumps(ev.payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        # Record in sync_event_inbox
        inbox_entry = SyncEventInbox(
            school_id=ev.school_id,
            event_id=ev.event_id,
            device_id=ev.device_id,
            event_type=ev.event_type,
            schema_version=ev.schema_version,
            payload_hash=payload_hash,
            status="processed",
            received_at=now,
            processed_at=now,
        )
        db.add(inbox_entry)

        # Record append-only authoritative learning_event
        learning_event = LearningEvent(
            id=ev.event_id,
            school_id=ev.school_id,
            user_id=ev.user_id,
            device_id=ev.device_id,
            event_type=ev.event_type,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            device_sequence=ev.device_sequence,
            schema_version=ev.schema_version,
            payload_json=ev.payload,
            occurred_at=ev.occurred_at,
            received_at=now,
            processed_at=now,
        )
        db.add(learning_event)

        # Monotonic projections based on event_type
        if ev.event_type == "lesson.started":
            _project_lesson_started(db, ev)
        elif ev.event_type == "lesson.progress_updated":
            _project_lesson_progress(db, ev)
        elif ev.event_type == "lesson.completed":
            _project_lesson_completed(db, ev)
        elif ev.event_type in ("note.created", "note.updated"):
            _project_note(db, ev)
        elif ev.event_type == "assessment.submitted":
            _project_assessment_submitted(db, ev)
        elif ev.event_type in ("content.downloaded", "content.verified"):
            _project_device_content(db, ev)

        if ev.device_sequence > max_sequence:
            max_sequence = ev.device_sequence

        acknowledged.append(ev.event_id)

    # Update device sync state
    sync_state = db.execute(
        select(DeviceSyncState).where(DeviceSyncState.device_id == req.device_id)
    ).scalar_one_or_none()
    if not sync_state:
        sync_state = DeviceSyncState(
            school_id=school_id,
            device_id=req.device_id,
            last_received_sequence=max_sequence,
            status="active",
            last_sync_at=now,
        )
        db.add(sync_state)
    else:
        if max_sequence > sync_state.last_received_sequence:
            sync_state.last_received_sequence = max_sequence
        sync_state.last_sync_at = now

    # Also update device last seen
    if device:
        device.last_seen_at = now

    db.commit()

    # Generate server cursor based on latest change log or timestamp
    last_log = (
        db.execute(
            select(ServerChangeLog)
            .where(ServerChangeLog.school_id == school_id)
            .order_by(ServerChangeLog.id.desc())
        )
        .scalars()
        .first()
    )
    cursor_id = last_log.id if last_log else 0
    server_cursor = f"cursor-{cursor_id}"

    if sync_state:
        sync_state.last_server_cursor = server_cursor
        db.commit()

    return SyncBatchResponse(
        batch_id=req.batch_id,
        protocol_version=req.protocol_version,
        acknowledged=acknowledged,
        duplicates=duplicates,
        rejected=rejected,
        requires_review=[],
        server_cursor=server_cursor,
    )


def _project_lesson_started(db: Session, ev):
    progress = db.execute(
        select(LessonProgress).where(
            LessonProgress.school_id == ev.school_id,
            LessonProgress.user_id == ev.user_id,
            LessonProgress.lesson_id == ev.entity_id,
        )
    ).scalar_one_or_none()

    if not progress:
        progress = LessonProgress(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            status="in_progress",
            completion_percentage=0.0,
            last_position_seconds=0,
            started_at=ev.occurred_at,
        )
        db.add(progress)
    elif progress.status == "not_started":
        progress.status = "in_progress"
        if not progress.started_at:
            progress.started_at = ev.occurred_at
    db.flush()


def _project_lesson_progress(db: Session, ev):
    try:
        new_pct = float(ev.payload.get("completion_percentage", 0.0))
        pos_sec = int(ev.payload.get("last_position_seconds", 0))
    except (ValueError, TypeError):
        new_pct = 0.0
        pos_sec = 0

    new_pct = max(0.0, min(100.0, new_pct))

    progress = db.execute(
        select(LessonProgress).where(
            LessonProgress.school_id == ev.school_id,
            LessonProgress.user_id == ev.user_id,
            LessonProgress.lesson_id == ev.entity_id,
        )
    ).scalar_one_or_none()

    if not progress:
        status_val = "completed" if new_pct >= 100.0 else "in_progress"
        completed_val = ev.occurred_at if new_pct >= 100.0 else None
        progress = LessonProgress(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            status=status_val,
            completion_percentage=new_pct,
            last_position_seconds=max(0, pos_sec),
            started_at=ev.occurred_at,
            completed_at=completed_val,
        )
        db.add(progress)
    else:
        # Monotonic: only increase progress percentage
        if new_pct > progress.completion_percentage:
            progress.completion_percentage = new_pct
        if pos_sec > 0:
            progress.last_position_seconds = pos_sec
        if progress.completion_percentage >= 100.0:
            progress.status = "completed"
            if not progress.completed_at:
                progress.completed_at = ev.occurred_at
        elif progress.status == "not_started":
            progress.status = "in_progress"
    db.flush()


def _project_lesson_completed(db: Session, ev):
    progress = db.execute(
        select(LessonProgress).where(
            LessonProgress.school_id == ev.school_id,
            LessonProgress.user_id == ev.user_id,
            LessonProgress.lesson_id == ev.entity_id,
        )
    ).scalar_one_or_none()

    if not progress:
        progress = LessonProgress(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            status="completed",
            completion_percentage=100.0,
            last_position_seconds=int(ev.payload.get("last_position_seconds", 0)),
            started_at=ev.occurred_at,
            completed_at=ev.occurred_at,
        )
        db.add(progress)
    else:
        progress.completion_percentage = 100.0
        progress.status = "completed"
        if not progress.completed_at:
            progress.completed_at = ev.occurred_at
    db.flush()


def _project_note(db: Session, ev):
    content_text = ev.payload.get("content", "")
    lesson_id = ev.payload.get("lesson_id", ev.entity_id)

    # Match by note id or fallback to lesson_id
    note = db.execute(
        select(StudentNote).where(
            StudentNote.id == ev.entity_id,
            StudentNote.school_id == ev.school_id,
            StudentNote.user_id == ev.user_id,
            StudentNote.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not note:
        note = db.execute(
            select(StudentNote).where(
                StudentNote.school_id == ev.school_id,
                StudentNote.user_id == ev.user_id,
                StudentNote.lesson_id == ev.entity_id,
                StudentNote.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

    if not note:
        note = StudentNote(
            id=ev.entity_id,
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=lesson_id,
            content=content_text,
            revision=1,
        )
        db.add(note)
    else:
        note.content = content_text
        note.revision += 1
    db.flush()


def _project_assessment_submitted(db: Session, ev):
    assessment_id = ev.entity_id
    assessment = db.execute(
        select(Assessment)
        .options(selectinload(Assessment.questions))
        .where(Assessment.id == assessment_id, Assessment.school_id == ev.school_id)
    ).scalar_one_or_none()
    if not assessment:
        return

    attempt_id = ev.payload.get("attempt_id") or ev.event_id

    # Check idempotency
    existing = db.execute(
        select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id)
    ).scalar_one_or_none()
    if existing:
        return

    # Check attempts limit
    prior_attempts_count = (
        db.execute(
            select(func.count(AssessmentAttempt.id)).where(
                AssessmentAttempt.assessment_id == assessment_id,
                AssessmentAttempt.user_id == ev.user_id,
                AssessmentAttempt.school_id == ev.school_id,
            )
        ).scalar()
        or 0
    )

    if prior_attempts_count >= assessment.attempts_allowed:
        return

    questions = {q.id: q for q in assessment.questions}

    started_at_raw = ev.payload.get("started_at")
    submitted_at_raw = ev.payload.get("submitted_at")
    started_at = ev.occurred_at
    submitted_at = ev.occurred_at
    if started_at_raw:
        try:
            started_at = datetime.fromisoformat(started_at_raw)
        except Exception:
            started_at = ev.occurred_at
    if submitted_at_raw:
        try:
            submitted_at = datetime.fromisoformat(submitted_at_raw)
        except Exception:
            submitted_at = ev.occurred_at

    total_score = 0.0
    max_score = sum(q.marks for q in questions.values())

    attempt = AssessmentAttempt(
        id=attempt_id,
        school_id=ev.school_id,
        assessment_id=assessment_id,
        user_id=ev.user_id,
        device_id=ev.device_id,
        attempt_number=prior_attempts_count + 1,
        status="graded",
        started_at=started_at,
        submitted_at=submitted_at,
        maximum_score=max_score,
        grading_status="automatic",
    )
    db.add(attempt)
    db.flush()

    raw_answers = ev.payload.get("answers", [])
    seen_questions = set()
    for ans_sub in raw_answers:
        if not isinstance(ans_sub, dict):
            continue
        q_id = ans_sub.get("question_id")
        if not q_id or q_id in seen_questions:
            continue
        seen_questions.add(q_id)

        q = questions.get(q_id)
        if not q:
            continue

        is_correct = False
        awarded = 0.0
        correct_ans = q.correct_answer_json
        sub_ans = ans_sub.get("answer_json")

        if isinstance(correct_ans, list) and isinstance(sub_ans, list):
            is_correct = sorted(
                [str(x).strip().lower() for x in correct_ans]
            ) == sorted([str(x).strip().lower() for x in sub_ans])
        elif str(correct_ans).strip().lower() == str(sub_ans).strip().lower():
            is_correct = True

        if is_correct:
            awarded = q.marks
            total_score += awarded

        answer_record = Answer(
            attempt_id=attempt.id,
            question_id=q.id,
            answer_json=sub_ans,
            awarded_marks=awarded,
            is_correct=is_correct,
            submitted_at=submitted_at,
        )
        db.add(answer_record)

    attempt.score = min(total_score, max_score)

    db.add(
        ServerChangeLog(
            school_id=ev.school_id,
            entity_type="assessment_attempt",
            entity_id=attempt.id,
            change_type="created",
            version=1,
        )
    )
    db.flush()


def _project_device_content(db: Session, ev):
    content_id = ev.entity_id
    version_id = ev.payload.get("version_id") or ev.payload.get("content_version_id")
    sha256 = ev.payload.get("sha256", "")
    local_path = ev.payload.get(
        "local_path", f"/storage/emulated/0/EduConnect/{content_id}"
    )

    if not version_id:
        v = (
            db.execute(
                select(ContentVersion)
                .where(ContentVersion.content_id == content_id)
                .order_by(ContentVersion.version_number.desc())
            )
            .scalars()
            .first()
        )
        if v:
            version_id = v.id
            if not sha256:
                sha256 = v.sha256
        else:
            return  # Unknown content

    status_val = "verified" if ev.event_type == "content.verified" else "downloading"
    if "status" in ev.payload:
        status_val = ev.payload["status"]

    record = db.execute(
        select(DeviceContent).where(
            DeviceContent.device_id == ev.device_id,
            DeviceContent.content_id == content_id,
        )
    ).scalar_one_or_none()

    if not record:
        record = DeviceContent(
            device_id=ev.device_id,
            content_id=content_id,
            content_version_id=version_id,
            sha256=sha256,
            local_path=local_path,
            status=status_val,
            downloaded_at=ev.occurred_at,
            last_accessed_at=ev.occurred_at,
        )
        db.add(record)
    else:
        record.content_version_id = version_id
        if sha256:
            record.sha256 = sha256
        if local_path:
            record.local_path = local_path
        record.status = status_val
        record.last_accessed_at = ev.occurred_at
        if status_val == "verified" and not record.downloaded_at:
            record.downloaded_at = ev.occurred_at
    db.flush()


def get_sync_status(db: Session, school_id: str, device_id: str) -> SyncStatusResponse:
    sync_state = db.execute(
        select(DeviceSyncState).where(
            DeviceSyncState.school_id == school_id,
            DeviceSyncState.device_id == device_id,
        )
    ).scalar_one_or_none()

    last_log = (
        db.execute(
            select(ServerChangeLog)
            .where(ServerChangeLog.school_id == school_id)
            .order_by(ServerChangeLog.id.desc())
        )
        .scalars()
        .first()
    )
    cursor_id = last_log.id if last_log else 0
    server_cursor = f"cursor-{cursor_id}"

    return SyncStatusResponse(
        protocol_version=1,
        server_time=datetime.now(UTC),
        device_id=device_id,
        last_sync_at=sync_state.last_sync_at if sync_state else None,
        last_processed_sequence=sync_state.last_received_sequence if sync_state else 0,
        server_cursor=server_cursor,
    )


def get_incremental_changes(
    db: Session, school_id: str, cursor_param: str | None = None
) -> SyncChangesResponse:
    cursor_id = 0
    if cursor_param:
        if cursor_param.startswith("cursor-"):
            try:
                cursor_id = int(cursor_param.replace("cursor-", ""))
            except ValueError:
                cursor_id = 0
        else:
            try:
                cursor_id = int(cursor_param)
            except ValueError:
                cursor_id = 0

    logs = (
        db.execute(
            select(ServerChangeLog)
            .where(
                ServerChangeLog.school_id == school_id,
                ServerChangeLog.id > cursor_id,
            )
            .order_by(ServerChangeLog.id.asc())
            .limit(100)
        )
        .scalars()
        .all()
    )

    changes = [
        ChangeItem(
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            change_type=log.change_type,
            version=log.version,
            created_at=log.created_at,
        )
        for log in logs
    ]

    new_cursor_id = logs[-1].id if logs else cursor_id
    new_cursor = f"cursor-{new_cursor_id}"

    return SyncChangesResponse(
        server_cursor=new_cursor,
        has_more=len(logs) == 100,
        changes=changes,
    )
