import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(UTC)


class SyncEventInbox(Base):
    __tablename__ = "sync_event_inbox"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id = Column(String(36), nullable=False, index=True)
    device_id = Column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(100), nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    payload_hash = Column(String(64), nullable=True)
    status = Column(
        String(20), default="processed", nullable=False
    )  # accepted, rejected, processed
    received_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    processed_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "school_id", "event_id", name="uq_sync_event_inbox_school_event"
        ),
    )

    school = relationship("School")
    device = relationship("Device")


class DeviceSyncState(Base):
    __tablename__ = "device_sync_states"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id = Column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    last_received_sequence = Column(Integer, default=0, nullable=False)
    last_server_cursor = Column(String(100), nullable=True)
    last_sync_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)
    status = Column(
        String(20), default="active", nullable=False
    )  # active, pending, failed

    school = relationship("School")
    device = relationship("Device")


class ServerChangeLog(Base):
    __tablename__ = "server_change_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False, index=True)
    change_type = Column(String(20), nullable=False)  # created, updated, deleted
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    school = relationship("School")
