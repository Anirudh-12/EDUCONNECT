from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, verify_device
from app.models.identity import User, Device
from app.modules.sync.schemas import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncStatusResponse,
    SyncChangesResponse,
)
from app.modules.sync import service

sync_router = APIRouter(prefix="/sync/v1", tags=["Synchronization"])


@sync_router.post("/events", response_model=SyncBatchResponse, summary="Ingest Event Batch (Idempotent)")
def ingest_events(
    req: SyncBatchRequest,
    current_user: User = Depends(get_current_user),
    device: Optional[Device] = Depends(verify_device),
    db: Session = Depends(get_db)
):
    return service.ingest_event_batch(db, current_user.school_id, current_user.id, req)


@sync_router.get("/status", response_model=SyncStatusResponse, summary="Get Sync Status")
def get_status(
    device_id: Optional[str] = Query(None, description="Device ID to check status for"),
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_device_id = device_id or x_device_id or "default-device"
    return service.get_sync_status(db, current_user.school_id, target_device_id)


@sync_router.get("/changes", response_model=SyncChangesResponse, summary="Get Incremental Changes Feed")
def get_changes(
    cursor: Optional[str] = Query(None, description="Cursor token"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return service.get_incremental_changes(db, current_user.school_id, cursor)
