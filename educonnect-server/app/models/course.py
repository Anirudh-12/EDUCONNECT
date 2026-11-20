import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=False)
    grade_level = Column(String(50), nullable=False)
    language = Column(String(10), default="en", nullable=False)
    thumbnail_content_id = Column(String(36), nullable=True)
    status = Column(
        String(20), default="draft", nullable=False
    )  # draft, published, archived
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    school = relationship("School")
    creator = relationship("User", foreign_keys=[created_by])
    lessons = relationship(
        "Lesson",
        back_populates="course",
        order_by="Lesson.sequence_number",
        cascade="all, delete-orphan",
    )
    enrollments = relationship(
        "CourseEnrollment", back_populates="course", cascade="all, delete-orphan"
    )


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrolled_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(
        String(20), default="active", nullable=False
    )  # active, completed, withdrawn

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_enrollment"),
    )

    school = relationship("School")
    course = relationship("Course", back_populates="enrollments")
    user = relationship("User")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        String(36),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    lesson_type = Column(
        String(20), default="document", nullable=False
    )  # video, document, audio, interactive, mixed
    sequence_number = Column(Integer, nullable=False)
    estimated_duration = Column(Integer, default=0, nullable=False)  # seconds
    status = Column(
        String(20), default="published", nullable=False
    )  # draft, published, archived
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    school = relationship("School")
    course = relationship("Course", back_populates="lessons")
    contents = relationship(
        "LessonContent",
        back_populates="lesson",
        order_by="LessonContent.sequence_number",
        cascade="all, delete-orphan",
    )


class LessonContent(Base):
    __tablename__ = "lesson_contents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = Column(
        String(36),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id = Column(
        String(36),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number = Column(Integer, default=1, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)

    school = relationship("School")
    lesson = relationship("Lesson", back_populates="contents")
    content = relationship("Content")
