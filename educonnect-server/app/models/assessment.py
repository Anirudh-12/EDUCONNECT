import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assessment_type = Column(String(20), default="quiz", nullable=False)  # quiz, test
    total_marks = Column(Float, default=0.0, nullable=False)
    passing_marks = Column(Float, nullable=True)
    time_limit_seconds = Column(Integer, nullable=True)
    attempts_allowed = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="published", nullable=False)  # draft, published, archived
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    school = relationship("School")
    course = relationship("Course")
    creator = relationship("User")
    questions = relationship("Question", back_populates="assessment", order_by="Question.sequence_number", cascade="all, delete-orphan")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type = Column(String(20), default="mcq", nullable=False)  # mcq, true_false, short_answer
    question_text = Column(Text, nullable=False)
    options_json = Column(JSON, nullable=True)
    correct_answer_json = Column(JSON, nullable=False)
    marks = Column(Float, default=1.0, nullable=False)
    sequence_number = Column(Integer, default=1, nullable=False)
    explanation = Column(Text, nullable=True)

    school = relationship("School")
    assessment = relationship("Assessment", back_populates="questions")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="graded", nullable=False)  # in_progress, submitted, graded
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True)
    maximum_score = Column(Float, default=0.0, nullable=False)
    grading_status = Column(String(20), default="automatic", nullable=False)  # pending, automatic, manual, reviewed

    school = relationship("School")
    assessment = relationship("Assessment", back_populates="attempts")
    user = relationship("User")
    device = relationship("Device")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_json = Column(JSON, nullable=False)
    awarded_marks = Column(Float, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    question = relationship("Question")
