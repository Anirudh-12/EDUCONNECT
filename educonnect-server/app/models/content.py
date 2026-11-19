import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Content(Base):
    __tablename__ = "contents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(20), default="pdf", nullable=False)  # pdf, video, audio, image, html, package
    mime_type = Column(String(100), nullable=False)
    language = Column(String(10), default="en", nullable=False)
    subject = Column(String(100), nullable=True)
    grade_level = Column(String(50), nullable=True)
    status = Column(String(20), default="published", nullable=False)  # draft, published, archived
    created_by = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    school = relationship("School")
    creator = relationship("User")
    versions = relationship("ContentVersion", back_populates="content", cascade="all, delete-orphan", order_by="ContentVersion.version_number.desc()")
    metadata_items = relationship("ContentMetadata", back_populates="content", cascade="all, delete-orphan")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, default=1, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("content_id", "version_number", name="uq_content_version"),
    )

    school = relationship("School")
    content = relationship("Content", back_populates="versions")


class ContentMetadata(Base):
    __tablename__ = "content_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    metadata_key = Column(String(100), nullable=False)
    metadata_value = Column(Text, nullable=False)

    content = relationship("Content", back_populates="metadata_items")


class DeviceContent(Base):
    __tablename__ = "device_contents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    content_version_id = Column(String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False)
    sha256 = Column(String(64), nullable=False)
    local_path = Column(String(500), nullable=False)
    status = Column(String(20), default="verified", nullable=False)  # downloading, verified, failed, deleted
    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    device = relationship("Device")
    content = relationship("Content")
    version = relationship("ContentVersion")


class TransferSession(Base):
    __tablename__ = "transfer_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    content_version_id = Column(String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False)
    source_device_id = Column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    bytes_transferred = Column(Integer, default=0, nullable=False)
    total_bytes = Column(Integer, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, transferring, completed, failed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    device = relationship("Device", foreign_keys=[device_id])
    source_device = relationship("Device", foreign_keys=[source_device_id])
    version = relationship("ContentVersion")
