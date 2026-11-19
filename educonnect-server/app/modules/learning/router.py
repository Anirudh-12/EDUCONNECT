from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.identity import User
from app.modules.learning.schemas import CourseListResponse, CourseItem, CourseLessonResponse
from app.modules.learning import service

learning_router = APIRouter(prefix="/courses", tags=["Classroom & Learning"])


@learning_router.get("", response_model=CourseListResponse, summary="List Courses")
def list_courses(
    status: Optional[str] = Query("published", description="Filter by course status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return service.list_courses(db, current_user.school_id, status_filter=status)


@learning_router.get("/{course_id}", response_model=CourseItem, summary="Get Course Details")
def get_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return service.get_course(db, current_user.school_id, course_id)


@learning_router.get("/{course_id}/lessons", response_model=CourseLessonResponse, summary="Get Course Lessons")
def get_course_lessons(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return service.get_course_lessons(db, current_user.school_id, course_id)
