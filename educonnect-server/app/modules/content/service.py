import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.content import Content, ContentVersion
from app.models.sync import ServerChangeLog
from app.modules.content.schemas import ContentManifestResponse, ManifestItem, ContentUploadResponse


def get_manifest(db: Session, school_id: str) -> ContentManifestResponse:
    contents = db.query(Content).filter(
        Content.school_id == school_id,
        Content.status == "published"
    ).all()

    items = []
    for c in contents:
        # Latest version
        version = db.query(ContentVersion).filter(
            ContentVersion.content_id == c.id
        ).order_by(ContentVersion.version_number.desc()).first()
        if not version:
            continue

        filename = Path(version.storage_path).name
        items.append(
            ManifestItem(
                content_id=c.id,
                version_id=version.id,
                filename=filename,
                mime_type=version.mime_type or c.mime_type,
                size_bytes=version.file_size_bytes,
                sha256=version.sha256,
                download_path=f"{settings.API_V1_PREFIX}/content/{c.id}/download"
            )
        )

    return ContentManifestResponse(
        school_id=school_id,
        generated_at=datetime.now(timezone.utc),
        items=items
    )


def get_content_file(db: Session, school_id: str, content_id: str) -> Tuple[Path, ContentVersion, Content]:
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.school_id == school_id
    ).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: The requested content resource does not exist."
        )

    version = db.query(ContentVersion).filter(
        ContentVersion.content_id == content.id
    ).order_by(ContentVersion.version_number.desc()).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: No published content version found."
        )

    file_path = Path(version.storage_path)
    if not file_path.is_absolute():
        # Check if relative to cwd or CONTENT_STORAGE_DIR
        candidate1 = Path.cwd() / file_path
        candidate2 = settings.CONTENT_STORAGE_DIR / file_path
        if candidate1.exists():
            file_path = candidate1
        elif candidate2.exists():
            file_path = candidate2
        else:
            file_path = settings.CONTENT_STORAGE_DIR / file_path.name

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RESOURCE_NOT_FOUND: Content binary file not found on server storage: {file_path.name}"
        )

    return file_path, version, content


def save_content(
    db: Session,
    school_id: str,
    user_id: str,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    title: Optional[str] = None,
    content_type: str = "pdf"
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
        created_by=user_id
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
        published_at=datetime.now(timezone.utc)
    )
    db.add(version)

    # Change log entry
    change_log = ServerChangeLog(
        school_id=school_id,
        entity_type="content",
        entity_id=content.id,
        change_type="created",
        version=1
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
        download_path=f"{settings.API_V1_PREFIX}/content/{content.id}/download"
    )
