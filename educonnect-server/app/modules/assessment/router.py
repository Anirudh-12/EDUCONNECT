from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.identity import User
from app.modules.assessment import service
from app.modules.assessment.schemas import (
    AssessmentStudentView,
    AttemptSubmitRequest,
    AttemptSubmitResponse,
)

assessment_router = APIRouter(prefix="/assessments", tags=["Assessments & Quizzes"])


@assessment_router.get(
    "/{assessment_id}",
    response_model=AssessmentStudentView,
    summary="Get Assessment (Student View)",
)
def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_assessment(db, current_user.school_id, assessment_id)


@assessment_router.post(
    "/{assessment_id}/attempts",
    response_model=AttemptSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Assessment Attempt",
)
def submit_attempt(
    assessment_id: str,
    req: AttemptSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.submit_attempt(
        db, current_user.school_id, current_user.id, assessment_id, req
    )
