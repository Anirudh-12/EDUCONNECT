from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.identity import User
from app.modules.content import service
from app.modules.content.schemas import ContentManifestResponse, ContentUploadResponse

content_router = APIRouter(prefix="/content", tags=["Content Management"])


def _stream_file_chunks(
    file_path: Path, start: int = 0, length: int | None = None, chunk_size: int = 65536
):
    """Yield file chunks without loading entire file into memory."""
    with open(file_path, "rb") as f:
        if start > 0:
            f.seek(start)
        remaining = length if length is not None else float("inf")
        while remaining > 0:
            bytes_to_read = (
                min(chunk_size, int(remaining)) if length is not None else chunk_size
            )
            chunk = f.read(bytes_to_read)
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


@content_router.get(
    "/manifest", response_model=ContentManifestResponse, summary="Get Content Manifest"
)
def get_content_manifest(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.get_manifest(db, current_user.school_id)


@content_router.get(
    "/{content_id}/download",
    summary="Download Content Binary (Supports Range Requests)",
)
def download_content(
    content_id: str,
    range: str | None = Header(None, alias="Range"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_path, version, content = service.get_content_file(
        db, current_user.school_id, content_id
    )
    total_size = file_path.stat().st_size
    mime_type = version.mime_type or content.mime_type or "application/octet-stream"
    sha256 = version.sha256

    common_headers = {
        "Accept-Ranges": "bytes",
        "ETag": f'"{sha256}"',
        "X-Content-SHA256": sha256,
    }

    if range:
        # Expected format: bytes=start-end or bytes=start-
        if not range.startswith("bytes="):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Range header format. Must start with 'bytes='",
            )

        range_val = range[6:].strip()
        parts = range_val.split("-", 1)
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Range header bounds",
            )

        start_str, end_str = parts[0].strip(), parts[1].strip()

        try:
            if start_str and end_str:
                start = int(start_str)
                end = int(end_str)
            elif start_str:
                start = int(start_str)
                end = total_size - 1
            elif end_str:
                # Suffix bytes e.g. -500
                suffix = int(end_str)
                start = max(0, total_size - suffix)
                end = total_size - 1
            else:
                start = 0
                end = total_size - 1
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Non-integer range bounds",
            )

        if start < 0 or start >= total_size or end < start:
            return Response(
                status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
                headers={"Content-Range": f"bytes */{total_size}"},
            )

        end = min(end, total_size - 1)
        chunk_length = end - start + 1

        headers = {
            **common_headers,
            "Content-Range": f"bytes {start}-{end}/{total_size}",
            "Content-Length": str(chunk_length),
            "Content-Type": mime_type,
        }
        return StreamingResponse(
            _stream_file_chunks(file_path, start=start, length=chunk_length),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers,
        )

    # Full content streaming download
    headers = {
        **common_headers,
        "Content-Length": str(total_size),
        "Content-Type": mime_type,
    }
    return StreamingResponse(
        _stream_file_chunks(file_path, start=0, length=total_size),
        status_code=status.HTTP_200_OK,
        headers=headers,
    )


@content_router.post(
    "/upload",
    response_model=ContentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Content Binary",
)
async def upload_content(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    content_type: str = Form("pdf"),
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    content_bytes = await file.read()
    filename = file.filename or "content.bin"
    mime_type = file.content_type or "application/octet-stream"

    return service.save_content(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        file_bytes=content_bytes,
        filename=filename,
        mime_type=mime_type,
        title=title,
        content_type=content_type,
    )
