from datetime import datetime

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
    description: str | None = None
    lesson_type: str
    sequence_number: int
    estimated_duration: int
    contents: list[ContentItemInLesson] = []

    model_config = ConfigDict(from_attributes=True)


class CourseLessonResponse(BaseModel):
    course_id: str
    lessons: list[LessonDetail]


class CourseItem(BaseModel):
    id: str
    school_id: str
    title: str
    description: str | None = None
    subject: str
    grade_level: str
    language: str
    thumbnail_content_id: str | None = None
    status: str
    lessons_count: int = 0
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    items: list[CourseItem]
    total: int


class CourseCreate(BaseModel):
    title: str
    description: str | None = None
    subject: str
    grade_level: str
    language: str = "en"
    thumbnail_content_id: str | None = None
    status: str = "published"


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    subject: str | None = None
    grade_level: str | None = None
    language: str | None = None
    thumbnail_content_id: str | None = None
    status: str | None = None


class LessonCreate(BaseModel):
    title: str
    description: str | None = None
    lesson_type: str = "document"  # video, document, audio, interactive, mixed
    sequence_number: int = 1
    estimated_duration: int = 0
    status: str = "published"


class LessonUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    lesson_type: str | None = None
    sequence_number: int | None = None
    estimated_duration: int | None = None
    status: str | None = None


class LessonContentAdd(BaseModel):
    content_id: str
    sequence_number: int = 1
    is_required: bool = True
