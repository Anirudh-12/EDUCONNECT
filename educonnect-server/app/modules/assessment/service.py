import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.assessment import Assessment, Question, AssessmentAttempt, Answer
from app.modules.assessment.schemas import (
    AssessmentStudentView,
    QuestionStudentView,
    AttemptSubmitRequest,
    AttemptSubmitResponse,
)


def get_assessment(db: Session, school_id: str, assessment_id: str) -> AssessmentStudentView:
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.school_id == school_id
    ).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Assessment not found"
        )

    questions = db.query(Question).filter(
        Question.assessment_id == assessment_id
    ).order_by(Question.sequence_number.asc()).all()

    question_views = [
        QuestionStudentView(
            id=q.id,
            question_type=q.question_type,
            question_text=q.question_text,
            options_json=q.options_json,
            marks=q.marks,
            sequence_number=q.sequence_number
        )
        for q in questions
    ]

    return AssessmentStudentView(
        id=assessment.id,
        title=assessment.title,
        time_limit_seconds=assessment.time_limit_seconds,
        total_marks=assessment.total_marks,
        questions=question_views
    )


def submit_attempt(
    db: Session,
    school_id: str,
    user_id: str,
    assessment_id: str,
    req: AttemptSubmitRequest
) -> AttemptSubmitResponse:
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.school_id == school_id
    ).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Assessment not found"
        )

    # Check idempotency: attempt_id already exists
    existing = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.id == req.attempt_id
    ).first()
    if existing:
        return AttemptSubmitResponse(
            attempt_id=existing.id,
            status=existing.status,
            score=existing.score or 0.0,
            maximum_score=existing.maximum_score,
            grading_status=existing.grading_status
        )

    questions = {
        q.id: q
        for q in db.query(Question).filter(Question.assessment_id == assessment_id).all()
    }

    total_score = 0.0
    max_score = sum(q.marks for q in questions.values())

    attempt = AssessmentAttempt(
        id=req.attempt_id,
        school_id=school_id,
        assessment_id=assessment_id,
        user_id=user_id,
        device_id=req.device_id,
        attempt_number=1,
        status="graded",
        started_at=req.started_at,
        submitted_at=req.submitted_at,
        maximum_score=max_score,
        grading_status="automatic"
    )
    db.add(attempt)
    db.flush()

    for ans_sub in req.answers:
        q = questions.get(ans_sub.question_id)
        if not q:
            continue

        is_correct = False
        awarded = 0.0

        # Automatic evaluation
        correct_ans = q.correct_answer_json
        sub_ans = ans_sub.answer_json

        # Normalise comparisons
        if str(correct_ans).strip().lower() == str(sub_ans).strip().lower():
            is_correct = True
            awarded = q.marks
            total_score += awarded

        answer_record = Answer(
            attempt_id=attempt.id,
            question_id=q.id,
            answer_json=ans_sub.answer_json,
            awarded_marks=awarded,
            is_correct=is_correct,
            submitted_at=req.submitted_at
        )
        db.add(answer_record)

    attempt.score = total_score
    db.commit()
    db.refresh(attempt)

    return AttemptSubmitResponse(
        attempt_id=attempt.id,
        status=attempt.status,
        score=attempt.score,
        maximum_score=attempt.maximum_score,
        grading_status=attempt.grading_status
    )
