from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ContentItemInLesson(BaseModel):
    content_id: str
    version_id: str
    title: str
    mime_type: str
    file_size_bytes: int
    sha256: str
    is_required: bool = True

    model_config = ConfigDict(from_attributes=True)


class LessonDetail(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    lesson_type: str
    sequence_number: int
    estimated_duration: int
    contents: List[ContentItemInLesson] = []

    model_config = ConfigDict(from_attributes=True)


class CourseLessonResponse(BaseModel):
    course_id: str
    lessons: List[LessonDetail]


class CourseItem(BaseModel):
    id: str
    school_id: str
    title: str
    description: Optional[str] = None
    subject: str
    grade_level: str
    language: str
    thumbnail_content_id: Optional[str] = None
    status: str
    lessons_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    items: List[CourseItem]
    total: int
