from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.identity import User
from app.modules.learning import service
from app.modules.learning.schemas import (
    ContentItemInLesson,
    CourseCreate,
    CourseItem,
    CourseLessonResponse,
    CourseListResponse,
    CourseUpdate,
    LessonContentAdd,
    LessonCreate,
    LessonDetail,
    LessonUpdate,
)

learning_router = APIRouter(prefix="/courses", tags=["Classroom & Learning"])


@learning_router.get("", response_model=CourseListResponse, summary="List Courses")
def list_courses(
    status: str | None = Query("published", description="Filter by course status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_courses(db, current_user.school_id, status_filter=status)


@learning_router.post(
    "",
    response_model=CourseItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create Course",
)
def create_course(
    data: CourseCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.create_course(db, current_user.school_id, current_user.id, data)


@learning_router.get(
    "/{course_id}", response_model=CourseItem, summary="Get Course Details"
)
def get_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_course(db, current_user.school_id, course_id)


@learning_router.put("/{course_id}", response_model=CourseItem, summary="Update Course")
def update_course(
    course_id: str,
    data: CourseUpdate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.update_course(db, current_user.school_id, course_id, data)


@learning_router.delete("/{course_id}", summary="Delete Course")
def delete_course(
    course_id: str,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.delete_course(db, current_user.school_id, course_id)


@learning_router.get(
    "/{course_id}/lessons",
    response_model=CourseLessonResponse,
    summary="Get Course Lessons",
)
def get_course_lessons(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_course_lessons(db, current_user.school_id, course_id)


@learning_router.post(
    "/{course_id}/lessons",
    response_model=LessonDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create Lesson",
)
def create_lesson(
    course_id: str,
    data: LessonCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.create_lesson(db, current_user.school_id, course_id, data)


@learning_router.put(
    "/{course_id}/lessons/{lesson_id}",
    response_model=LessonDetail,
    summary="Update Lesson",
)
def update_lesson(
    course_id: str,
    lesson_id: str,
    data: LessonUpdate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.update_lesson(db, current_user.school_id, course_id, lesson_id, data)


@learning_router.delete("/{course_id}/lessons/{lesson_id}", summary="Delete Lesson")
def delete_lesson(
    course_id: str,
    lesson_id: str,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.delete_lesson(db, current_user.school_id, course_id, lesson_id)


@learning_router.post(
    "/{course_id}/lessons/{lesson_id}/content",
    response_model=ContentItemInLesson,
    status_code=status.HTTP_201_CREATED,
    summary="Add Content to Lesson",
)
def add_lesson_content(
    course_id: str,
    lesson_id: str,
    data: LessonContentAdd,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.add_lesson_content(
        db, current_user.school_id, course_id, lesson_id, data
    )
