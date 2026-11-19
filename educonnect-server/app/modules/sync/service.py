import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.sync import SyncEventInbox, DeviceSyncState, ServerChangeLog
from app.models.learning import LearningEvent, LessonProgress, StudentNote
from app.models.identity import Device, User
from app.modules.sync.schemas import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncChangesResponse,
    ChangeItem,
    SyncStatusResponse,
)


def ingest_event_batch(db: Session, school_id: str, caller_user_id: str, req: SyncBatchRequest) -> SyncBatchResponse:
    # Verify device exists and not revoked
    device = db.query(Device).filter(Device.id == req.device_id).first()
    if device and device.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEVICE_REVOKED: This device has been revoked and cannot submit sync events"
        )

    acknowledged: List[str] = []
    duplicates: List[str] = []
    rejected: List[str] = []
    now = datetime.now(timezone.utc)
    max_sequence = 0

    for ev in req.events:
        # Check idempotency: unique constraint on (school_id, event_id)
        existing_inbox = db.query(SyncEventInbox).filter(
            SyncEventInbox.school_id == ev.school_id,
            SyncEventInbox.event_id == ev.event_id
        ).first()

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
            processed_at=now
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
            processed_at=now
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

        if ev.device_sequence > max_sequence:
            max_sequence = ev.device_sequence

        acknowledged.append(ev.event_id)

    # Update device sync state
    sync_state = db.query(DeviceSyncState).filter(DeviceSyncState.device_id == req.device_id).first()
    if not sync_state:
        sync_state = DeviceSyncState(
            school_id=school_id,
            device_id=req.device_id,
            last_received_sequence=max_sequence,
            status="active",
            last_sync_at=now
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
    last_log = db.query(ServerChangeLog).filter(ServerChangeLog.school_id == school_id).order_by(ServerChangeLog.id.desc()).first()
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
        server_cursor=server_cursor
    )


def _project_lesson_started(db: Session, ev):
    progress = db.query(LessonProgress).filter(
        LessonProgress.school_id == ev.school_id,
        LessonProgress.user_id == ev.user_id,
        LessonProgress.lesson_id == ev.entity_id
    ).first()

    if not progress:
        progress = LessonProgress(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            status="in_progress",
            completion_percentage=0.0,
            last_position_seconds=0,
            started_at=ev.occurred_at
        )
        db.add(progress)
    elif progress.status == "not_started":
        progress.status = "in_progress"
        if not progress.started_at:
            progress.started_at = ev.occurred_at
    db.flush()


def _project_lesson_progress(db: Session, ev):
    new_pct = float(ev.payload.get("completion_percentage", 0.0))
    pos_sec = int(ev.payload.get("last_position_seconds", 0))

    progress = db.query(LessonProgress).filter(
        LessonProgress.school_id == ev.school_id,
        LessonProgress.user_id == ev.user_id,
        LessonProgress.lesson_id == ev.entity_id
    ).first()

    if not progress:
        status_val = "completed" if new_pct >= 100.0 else "in_progress"
        completed_val = ev.occurred_at if new_pct >= 100.0 else None
        progress = LessonProgress(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            status=status_val,
            completion_percentage=new_pct,
            last_position_seconds=pos_sec,
            started_at=ev.occurred_at,
            completed_at=completed_val
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
    progress = db.query(LessonProgress).filter(
        LessonProgress.school_id == ev.school_id,
        LessonProgress.user_id == ev.user_id,
        LessonProgress.lesson_id == ev.entity_id
    ).first()

    if not progress:
        progress = LessonProgress(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            status="completed",
            completion_percentage=100.0,
            last_position_seconds=int(ev.payload.get("last_position_seconds", 0)),
            started_at=ev.occurred_at,
            completed_at=ev.occurred_at
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
    note = db.query(StudentNote).filter(
        StudentNote.school_id == ev.school_id,
        StudentNote.user_id == ev.user_id,
        StudentNote.lesson_id == ev.entity_id,
        StudentNote.deleted_at.is_(None)
    ).first()

    if not note:
        note = StudentNote(
            school_id=ev.school_id,
            user_id=ev.user_id,
            lesson_id=ev.entity_id,
            content=content_text,
            revision=1
        )
        db.add(note)
    else:
        note.content = content_text
        note.revision += 1
    db.flush()


def get_sync_status(db: Session, school_id: str, device_id: str) -> SyncStatusResponse:
    sync_state = db.query(DeviceSyncState).filter(
        DeviceSyncState.school_id == school_id,
        DeviceSyncState.device_id == device_id
    ).first()

    last_log = db.query(ServerChangeLog).filter(
        ServerChangeLog.school_id == school_id
    ).order_by(ServerChangeLog.id.desc()).first()
    cursor_id = last_log.id if last_log else 0
    server_cursor = f"cursor-{cursor_id}"

    return SyncStatusResponse(
        protocol_version=1,
        server_time=datetime.now(timezone.utc),
        device_id=device_id,
        last_sync_at=sync_state.last_sync_at if sync_state else None,
        last_processed_sequence=sync_state.last_received_sequence if sync_state else 0,
        server_cursor=server_cursor
    )


def get_incremental_changes(db: Session, school_id: str, cursor_param: Optional[str] = None) -> SyncChangesResponse:
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

    logs = db.query(ServerChangeLog).filter(
        ServerChangeLog.school_id == school_id,
        ServerChangeLog.id > cursor_id
    ).order_by(ServerChangeLog.id.asc()).limit(100).all()

    changes = [
        ChangeItem(
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            change_type=log.change_type,
            version=log.version,
            created_at=log.created_at
        )
        for log in logs
    ]

    new_cursor_id = logs[-1].id if logs else cursor_id
    new_cursor = f"cursor-{new_cursor_id}"

    return SyncChangesResponse(
        server_cursor=new_cursor,
        has_more=len(logs) == 100,
        changes=changes
    )
