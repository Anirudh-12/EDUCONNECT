from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.course import Course, Lesson, LessonContent
from app.models.content import Content, ContentVersion
from app.modules.learning.schemas import (
    CourseItem,
    CourseListResponse,
    LessonDetail,
    ContentItemInLesson,
    CourseLessonResponse,
)


def list_courses(db: Session, school_id: str, status_filter: Optional[str] = "published") -> CourseListResponse:
    query = db.query(Course).filter(Course.school_id == school_id)
    if status_filter:
        query = query.filter(Course.status == status_filter)

    courses = query.order_by(Course.created_at.desc()).all()
    items = []
    for c in courses:
        lessons_count = db.query(Lesson).filter(Lesson.course_id == c.id).count()
        items.append(
            CourseItem(
                id=c.id,
                school_id=c.school_id,
                title=c.title,
                description=c.description,
                subject=c.subject,
                grade_level=c.grade_level,
                language=c.language,
                thumbnail_content_id=c.thumbnail_content_id,
                status=c.status,
                lessons_count=lessons_count,
                updated_at=c.updated_at
            )
        )
    return CourseListResponse(items=items, total=len(items))


def get_course(db: Session, school_id: str, course_id: str) -> CourseItem:
    c = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == school_id
    ).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found."
        )
    lessons_count = db.query(Lesson).filter(Lesson.course_id == c.id).count()
    return CourseItem(
        id=c.id,
        school_id=c.school_id,
        title=c.title,
        description=c.description,
        subject=c.subject,
        grade_level=c.grade_level,
        language=c.language,
        thumbnail_content_id=c.thumbnail_content_id,
        status=c.status,
        lessons_count=lessons_count,
        updated_at=c.updated_at
    )


def get_course_lessons(db: Session, school_id: str, course_id: str) -> CourseLessonResponse:
    c = db.query(Course).filter(
        Course.id == course_id,
        Course.school_id == school_id
    ).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found."
        )

    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id
    ).order_by(Lesson.sequence_number.asc()).all()

    lesson_details: List[LessonDetail] = []
    for l in lessons:
        lesson_contents = db.query(LessonContent).filter(
            LessonContent.lesson_id == l.id
        ).order_by(LessonContent.sequence_number.asc()).all()

        content_items: List[ContentItemInLesson] = []
        for lc in lesson_contents:
            content = db.query(Content).filter(Content.id == lc.content_id).first()
            if not content:
                continue
            # Get latest content version
            version = db.query(ContentVersion).filter(
                ContentVersion.content_id == content.id
            ).order_by(ContentVersion.version_number.desc()).first()

            if version:
                content_items.append(
                    ContentItemInLesson(
                        content_id=content.id,
                        version_id=version.id,
                        title=content.title,
                        mime_type=version.mime_type or content.mime_type,
                        file_size_bytes=version.file_size_bytes,
                        sha256=version.sha256,
                        is_required=lc.is_required
                    )
                )

        lesson_details.append(
            LessonDetail(
                id=l.id,
                title=l.title,
                description=l.description,
                lesson_type=l.lesson_type,
                sequence_number=l.sequence_number,
                estimated_duration=l.estimated_duration,
                contents=content_items
            )
        )

    return CourseLessonResponse(
        course_id=course_id,
        lessons=lesson_details
    )
