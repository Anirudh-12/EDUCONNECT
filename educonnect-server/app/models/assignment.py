import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    classroom_id = Column(
        String(36),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        String(36),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status = Column(
        String(20), default="published", nullable=False
    )  # draft, published, closed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    school = relationship("School")
    classroom = relationship("Classroom")
    course = relationship("Course")
    creator = relationship("User", foreign_keys=[created_by])
    submissions = relationship(
        "AssignmentSubmission",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignment_id = Column(
        String(36),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id = Column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submission_text = Column(Text, nullable=True)
    attachments_json = Column(JSON, default=list, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(
        String(20), default="submitted", nullable=False
    )  # submitted, late, graded, returned
    marks = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    graded_at = Column(DateTime(timezone=True), nullable=True)

    school = relationship("School")
    assignment = relationship("Assignment", back_populates="submissions")
    user = relationship("User", foreign_keys=[user_id])
    device = relationship("Device")
    grader = relationship("User", foreign_keys=[graded_by])
