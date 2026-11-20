import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class School(Base):
    __tablename__ = "schools"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)
    settings_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
