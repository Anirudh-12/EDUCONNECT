import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    grade_level = Column(String(50), nullable=False)
    section = Column(String(50), nullable=True)
    academic_year = Column(String(50), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, archived
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    school = relationship("School")
    memberships = relationship("ClassroomMembership", back_populates="classroom", cascade="all, delete-orphan")


class ClassroomMembership(Base):
    __tablename__ = "classroom_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    membership_role = Column(String(20), nullable=False)  # student, teacher
    joined_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    left_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("classroom_id", "user_id", name="uq_classroom_membership"),
    )

    school = relationship("School")
    classroom = relationship("Classroom", back_populates="memberships")
    user = relationship("User")
