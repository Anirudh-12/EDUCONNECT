from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import Answer, Assessment, AssessmentAttempt
from app.modules.assessment.schemas import (
    AssessmentStudentView,
    AttemptSubmitRequest,
    AttemptSubmitResponse,
    QuestionStudentView,
)


def get_assessment(
    db: Session, school_id: str, assessment_id: str
) -> AssessmentStudentView:
    assessment = db.execute(
        select(Assessment)
        .options(selectinload(Assessment.questions))
        .where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    ).scalar_one_or_none()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Assessment not found",
        )

    question_views = [
        QuestionStudentView(
            id=q.id,
            question_type=q.question_type,
            question_text=q.question_text,
            options_json=q.options_json,
            marks=q.marks,
            sequence_number=q.sequence_number,
        )
        for q in assessment.questions
    ]

    return AssessmentStudentView(
        id=assessment.id,
        title=assessment.title,
        time_limit_seconds=assessment.time_limit_seconds,
        total_marks=assessment.total_marks,
        questions=question_views,
    )


def submit_attempt(
    db: Session,
    school_id: str,
    user_id: str,
    assessment_id: str,
    req: AttemptSubmitRequest,
) -> AttemptSubmitResponse:
    assessment = db.execute(
        select(Assessment)
        .options(selectinload(Assessment.questions))
        .where(Assessment.id == assessment_id, Assessment.school_id == school_id)
    ).scalar_one_or_none()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Assessment not found",
        )

    if assessment.status != "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"PERMISSION_DENIED: Assessment is {assessment.status}",
        )

    # Check idempotency: attempt_id already exists
    existing = db.execute(
        select(AssessmentAttempt).where(AssessmentAttempt.id == req.attempt_id)
    ).scalar_one_or_none()
    if existing:
        if existing.user_id != user_id or existing.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PERMISSION_DENIED: Attempt ID mismatch or unauthorized",
            )
        return AttemptSubmitResponse(
            attempt_id=existing.id,
            status=existing.status,
            score=existing.score or 0.0,
            maximum_score=existing.maximum_score,
            grading_status=existing.grading_status,
        )

    # Check attempts limit
    prior_attempts_count = (
        db.execute(
            select(func.count(AssessmentAttempt.id)).where(
                AssessmentAttempt.assessment_id == assessment_id,
                AssessmentAttempt.user_id == user_id,
                AssessmentAttempt.school_id == school_id,
            )
        ).scalar()
        or 0
    )

    if prior_attempts_count >= assessment.attempts_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Maximum attempts limit reached: Allowed {assessment.attempts_allowed}, "
                f"completed {prior_attempts_count}"
            ),
        )

    now = datetime.now(UTC)
    questions_by_id = {q.id: q for q in assessment.questions}

    # Grade answers deterministically - deduplicating repeated question answers
    total_score = 0.0
    answer_records = []
    seen_question_ids = set()

    for ans_input in req.answers:
        if ans_input.question_id in seen_question_ids:
            continue
        seen_question_ids.add(ans_input.question_id)

        q = questions_by_id.get(ans_input.question_id)
        if not q:
            continue

        is_correct = False
        marks_awarded = 0.0

        if isinstance(q.correct_answer_json, dict) and isinstance(ans_input.answer_json, dict):
            if q.question_type == "mcq":
                correct_val = q.correct_answer_json.get("correct_option_id")
                selected_val = ans_input.answer_json.get("selected_option_id")
                if correct_val is not None and selected_val == correct_val:
                    is_correct = True
                    marks_awarded = q.marks
            elif q.question_type == "true_false":
                correct_val = q.correct_answer_json.get("value")
                selected_val = ans_input.answer_json.get("value")
                if correct_val is not None and selected_val == correct_val:
                    is_correct = True
                    marks_awarded = q.marks
            elif q.question_type == "short_answer":
                expected = str(q.correct_answer_json.get("text", "")).strip().lower()
                actual = str(ans_input.answer_json.get("text", "")).strip().lower()
                if expected and actual == expected:
                    is_correct = True
                    marks_awarded = q.marks
        elif isinstance(q.correct_answer_json, list) and isinstance(ans_input.answer_json, list):
            if sorted([str(x).strip().lower() for x in q.correct_answer_json]) == sorted(
                [str(x).strip().lower() for x in ans_input.answer_json]
            ):
                is_correct = True
                marks_awarded = q.marks
        else:
            if str(q.correct_answer_json).strip().lower() == str(ans_input.answer_json).strip().lower():
                is_correct = True
                marks_awarded = q.marks

        total_score += marks_awarded

        ans_record = Answer(
            attempt_id=req.attempt_id,
            question_id=q.id,
            answer_json=ans_input.answer_json,
            is_correct=is_correct,
            awarded_marks=marks_awarded,
            submitted_at=req.submitted_at or now,
        )
        answer_records.append(ans_record)

    attempt_number = prior_attempts_count + 1
    new_attempt = AssessmentAttempt(
        id=req.attempt_id,
        school_id=school_id,
        assessment_id=assessment_id,
        user_id=user_id,
        device_id=req.device_id,
        attempt_number=attempt_number,
        status="graded",
        score=total_score,
        maximum_score=assessment.total_marks,
        grading_status="automatic",
        started_at=req.started_at,
        submitted_at=req.submitted_at or now,
    )
    db.add(new_attempt)
    db.flush()

    for ans in answer_records:
        db.add(ans)

    db.commit()
    db.refresh(new_attempt)

    return AttemptSubmitResponse(
        attempt_id=new_attempt.id,
        status=new_attempt.status,
        score=new_attempt.score,
        maximum_score=new_attempt.maximum_score,
        grading_status=new_attempt.grading_status,
    )
