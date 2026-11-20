from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ManifestItem(BaseModel):
    content_id: str
    version_id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    download_path: str

    model_config = ConfigDict(from_attributes=True)


class ContentManifestResponse(BaseModel):
    school_id: str
    generated_at: datetime
    items: list[ManifestItem]


class ContentUploadResponse(BaseModel):
    content_id: str
    version_id: str
    title: str
    filename: str
    mime_type: str
    file_size_bytes: int
    sha256: str
    download_path: str
