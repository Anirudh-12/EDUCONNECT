from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Content
from app.models.course import Course, Lesson, LessonContent
from app.models.sync import ServerChangeLog
from app.modules.content.service import get_content_with_latest_version
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


def list_courses(
    db: Session, school_id: str, status_filter: str | None = "published"
) -> CourseListResponse:
    query = select(Course).where(Course.school_id == school_id)
    if status_filter:
        query = query.where(Course.status == status_filter)

    courses = db.execute(query.order_by(Course.created_at.desc())).scalars().all()
    if not courses:
        return CourseListResponse(items=[], total=0)

    course_ids = [c.id for c in courses]
    count_rows = db.execute(
        select(Lesson.course_id, func.count(Lesson.id))
        .where(Lesson.course_id.in_(course_ids))
        .group_by(Lesson.course_id)
    ).all()
    lesson_counts = {cid: cnt for cid, cnt in count_rows}

    items = [
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
            lessons_count=lesson_counts.get(c.id, 0),
            updated_at=c.updated_at,
        )
        for c in courses
    ]
    return CourseListResponse(items=items, total=len(items))


def get_course(db: Session, school_id: str, course_id: str) -> CourseItem:
    c = db.execute(
        select(Course).where(Course.id == course_id, Course.school_id == school_id)
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found.",
        )
    lessons_count = (
        db.execute(
            select(func.count(Lesson.id)).where(Lesson.course_id == c.id)
        ).scalar()
        or 0
    )
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
        updated_at=c.updated_at,
    )


def get_course_lessons(
    db: Session, school_id: str, course_id: str
) -> CourseLessonResponse:
    c = db.execute(
        select(Course).where(Course.id == course_id, Course.school_id == school_id)
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found.",
        )

    lessons = (
        db.execute(
            select(Lesson)
            .options(
                selectinload(Lesson.contents)
                .selectinload(LessonContent.content)
                .selectinload(Content.versions)
            )
            .where(Lesson.course_id == course_id)
            .order_by(Lesson.sequence_number.asc())
        )
        .scalars()
        .all()
    )

    lesson_details: list[LessonDetail] = []
    for lesson in lessons:
        content_items: list[ContentItemInLesson] = []
        for lc in lesson.contents:
            content = lc.content
            if not content:
                continue
            version = content.versions[0] if content.versions else None
            if version:
                content_items.append(
                    ContentItemInLesson(
                        content_id=content.id,
                        version_id=version.id,
                        title=content.title,
                        mime_type=version.mime_type or content.mime_type,
                        file_size_bytes=version.file_size_bytes,
                        sha256=version.sha256,
                        is_required=lc.is_required,
                    )
                )

        lesson_details.append(
            LessonDetail(
                id=lesson.id,
                title=lesson.title,
                description=lesson.description,
                lesson_type=lesson.lesson_type,
                sequence_number=lesson.sequence_number,
                estimated_duration=lesson.estimated_duration,
                contents=content_items,
            )
        )

    return CourseLessonResponse(course_id=course_id, lessons=lesson_details)


def create_course(
    db: Session, school_id: str, user_id: str, data: CourseCreate
) -> CourseItem:
    course = Course(
        school_id=school_id,
        title=data.title,
        description=data.description,
        subject=data.subject,
        grade_level=data.grade_level,
        language=data.language,
        thumbnail_content_id=data.thumbnail_content_id,
        status=data.status,
        created_by=user_id,
        published_at=datetime.now(UTC) if data.status == "published" else None,
    )
    db.add(course)
    db.flush()

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="course",
            entity_id=course.id,
            change_type="created",
            version=1,
        )
    )
    db.commit()
    db.refresh(course)
    return get_course(db, school_id, course.id)


def update_course(
    db: Session, school_id: str, course_id: str, data: CourseUpdate
) -> CourseItem:
    c = db.execute(
        select(Course).where(Course.id == course_id, Course.school_id == school_id)
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found.",
        )
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(c, field, val)

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="course",
            entity_id=c.id,
            change_type="updated",
            version=2,
        )
    )
    db.commit()
    db.refresh(c)
    return get_course(db, school_id, c.id)


def delete_course(db: Session, school_id: str, course_id: str) -> dict:
    c = db.execute(
        select(Course).where(Course.id == course_id, Course.school_id == school_id)
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found.",
        )
    db.delete(c)
    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="course",
            entity_id=course_id,
            change_type="deleted",
            version=3,
        )
    )
    db.commit()
    return {"detail": "Course deleted successfully"}


def create_lesson(
    db: Session, school_id: str, course_id: str, data: LessonCreate
) -> LessonDetail:
    c = db.execute(
        select(Course).where(Course.id == course_id, Course.school_id == school_id)
    ).scalar_one_or_none()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested course could not be found.",
        )
    lesson = Lesson(
        school_id=school_id,
        course_id=course_id,
        title=data.title,
        description=data.description,
        lesson_type=data.lesson_type,
        sequence_number=data.sequence_number,
        estimated_duration=data.estimated_duration,
        status=data.status,
    )
    db.add(lesson)
    db.flush()

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="lesson",
            entity_id=lesson.id,
            change_type="created",
            version=1,
        )
    )
    db.commit()
    db.refresh(lesson)
    return LessonDetail(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        lesson_type=lesson.lesson_type,
        sequence_number=lesson.sequence_number,
        estimated_duration=lesson.estimated_duration,
        contents=[],
    )


def update_lesson(
    db: Session,
    school_id: str,
    course_id: str,
    lesson_id: str,
    data: LessonUpdate,
) -> LessonDetail:
    lesson = db.execute(
        select(Lesson).where(
            Lesson.id == lesson_id,
            Lesson.course_id == course_id,
            Lesson.school_id == school_id,
        )
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Lesson not found",
        )
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(lesson, field, val)

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="lesson",
            entity_id=lesson.id,
            change_type="updated",
            version=2,
        )
    )
    db.commit()
    db.refresh(lesson)
    return LessonDetail(
        id=lesson.id,
        title=lesson.title,
        description=lesson.description,
        lesson_type=lesson.lesson_type,
        sequence_number=lesson.sequence_number,
        estimated_duration=lesson.estimated_duration,
        contents=[],
    )


def delete_lesson(db: Session, school_id: str, course_id: str, lesson_id: str) -> dict:
    lesson = db.execute(
        select(Lesson).where(
            Lesson.id == lesson_id,
            Lesson.course_id == course_id,
            Lesson.school_id == school_id,
        )
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Lesson not found",
        )
    db.delete(lesson)
    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="lesson",
            entity_id=lesson_id,
            change_type="deleted",
            version=3,
        )
    )
    db.commit()
    return {"detail": "Lesson deleted successfully"}


def add_lesson_content(
    db: Session,
    school_id: str,
    course_id: str,
    lesson_id: str,
    data: LessonContentAdd,
) -> ContentItemInLesson:
    lesson = db.execute(
        select(Lesson).where(
            Lesson.id == lesson_id,
            Lesson.course_id == course_id,
            Lesson.school_id == school_id,
        )
    ).scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Lesson not found",
        )

    content, version = get_content_with_latest_version(db, school_id, data.content_id)

    mapping = LessonContent(
        school_id=school_id,
        lesson_id=lesson_id,
        content_id=data.content_id,
        sequence_number=data.sequence_number,
        is_required=data.is_required,
    )
    db.add(mapping)
    db.flush()

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="lesson_content",
            entity_id=mapping.id,
            change_type="created",
            version=1,
        )
    )
    db.commit()
    return ContentItemInLesson(
        content_id=content.id,
        version_id=version.id,
        title=content.title,
        mime_type=version.mime_type or content.mime_type,
        file_size_bytes=version.file_size_bytes,
        sha256=version.sha256,
        is_required=mapping.is_required,
    )
