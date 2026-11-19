from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class SyncEventSchema(BaseModel):
    event_id: str
    event_type: str
    schema_version: int = 1
    school_id: str
    user_id: str
    device_id: str
    entity_type: str
    entity_id: str
    device_sequence: int
    occurred_at: datetime
    recorded_at: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)


class SyncBatchRequest(BaseModel):
    protocol_version: int = 1
    device_id: str
    batch_id: str
    events: List[SyncEventSchema]


class SyncBatchResponse(BaseModel):
    batch_id: str
    protocol_version: int = 1
    acknowledged: List[str] = Field(default_factory=list)
    duplicates: List[str] = Field(default_factory=list)
    rejected: List[str] = Field(default_factory=list)
    requires_review: List[str] = Field(default_factory=list)
    server_cursor: str


class ChangeItem(BaseModel):
    entity_type: str
    entity_id: str
    change_type: str
    version: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SyncChangesResponse(BaseModel):
    server_cursor: str
    has_more: bool = False
    changes: List[ChangeItem]


class SyncStatusResponse(BaseModel):
    protocol_version: int = 1
    server_time: datetime
    device_id: str
    last_sync_at: Optional[datetime] = None
    last_processed_sequence: int = 0
    server_cursor: str
