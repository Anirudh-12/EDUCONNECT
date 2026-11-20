import hashlib
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.content import Content, ContentVersion
from app.models.sync import ServerChangeLog
from app.modules.content.schemas import (
    ContentManifestResponse,
    ContentUploadResponse,
    ManifestItem,
)


def get_manifest(db: Session, school_id: str) -> ContentManifestResponse:
    contents = (
        db.execute(
            select(Content)
            .options(selectinload(Content.versions))
            .where(Content.school_id == school_id, Content.status == "published")
        )
        .scalars()
        .all()
    )

    items = []
    for c in contents:
        if not c.versions:
            continue
        # Versions are ordered by version_number desc in relationship definition
        version = c.versions[0]
        filename = Path(version.storage_path).name
        items.append(
            ManifestItem(
                content_id=c.id,
                version_id=version.id,
                filename=filename,
                mime_type=version.mime_type or c.mime_type,
                size_bytes=version.file_size_bytes,
                sha256=version.sha256,
                download_path=f"{settings.API_V1_PREFIX}/content/{c.id}/download",
            )
        )

    return ContentManifestResponse(
        school_id=school_id,
        generated_at=datetime.now(UTC),
        items=items,
    )


def get_content_with_latest_version(
    db: Session, school_id: str, content_id: str
) -> tuple[Content, ContentVersion]:
    content = db.execute(
        select(Content)
        .options(selectinload(Content.versions))
        .where(Content.id == content_id, Content.school_id == school_id)
    ).scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Content not found",
        )
    if not content.versions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: No content version found",
        )
    return content, content.versions[0]


def get_content_file(
    db: Session, school_id: str, content_id: str
) -> tuple[Path, ContentVersion, Content]:
    content, version = get_content_with_latest_version(db, school_id, content_id)

    storage_root = settings.CONTENT_STORAGE_DIR.resolve()
    file_path = Path(version.storage_path)
    if not file_path.is_absolute():
        candidate1 = (Path.cwd() / file_path).resolve()
        candidate2 = (settings.CONTENT_STORAGE_DIR / file_path).resolve()
        candidate3 = (settings.CONTENT_STORAGE_DIR / file_path.name).resolve()
        if candidate3.exists():
            file_path = candidate3
        elif candidate1.exists():
            file_path = candidate1
        elif candidate2.exists():
            file_path = candidate2
        else:
            file_path = candidate3
    else:
        file_path = file_path.resolve()

    # Enforce safe directory boundary
    if not (
        file_path.is_relative_to(storage_root)
        or file_path.is_relative_to(Path.cwd().resolve())
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PERMISSION_DENIED: Access outside storage directory forbidden",
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RESOURCE_NOT_FOUND: Content binary file not found on server storage: {file_path.name}",
        )

    return file_path, version, content


def save_content(
    db: Session,
    school_id: str,
    user_id: str,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    title: str | None = None,
    content_type: str = "pdf",
) -> ContentUploadResponse:
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    file_size = len(file_bytes)

    # Destination storage path
    storage_dir = settings.CONTENT_STORAGE_DIR
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{sha256_hash}_{Path(filename).name}"
    target_file = storage_dir / stored_filename
    target_file.write_bytes(file_bytes)

    rel_storage_path = str(Path("storage/content") / stored_filename)

    # Create Content record
    content_title = title or filename
    content = Content(
        school_id=school_id,
        title=content_title,
        content_type=content_type,
        mime_type=mime_type,
        language="en",
        status="published",
        created_by=user_id,
    )
    db.add(content)
    db.flush()

    # Create ContentVersion
    version = ContentVersion(
        school_id=school_id,
        content_id=content.id,
        version_number=1,
        sha256=sha256_hash,
        storage_path=rel_storage_path,
        file_size_bytes=file_size,
        mime_type=mime_type,
        published_at=datetime.now(UTC),
    )
    db.add(version)

    # Change log entry
    change_log = ServerChangeLog(
        school_id=school_id,
        entity_type="content",
        entity_id=content.id,
        change_type="created",
        version=1,
    )
    db.add(change_log)

    db.commit()
    db.refresh(content)
    db.refresh(version)

    return ContentUploadResponse(
        content_id=content.id,
        version_id=version.id,
        title=content.title,
        filename=filename,
        mime_type=mime_type,
        file_size_bytes=file_size,
        sha256=sha256_hash,
        download_path=f"{settings.API_V1_PREFIX}/content/{content.id}/download",
    )
