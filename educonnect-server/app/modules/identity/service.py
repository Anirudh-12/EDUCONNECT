from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.identity import User, Device
from app.models.sync import DeviceSyncState
from app.modules.identity.schemas import LoginRequest, LoginResponse, UserSummary, TokenRefreshResponse, DeviceRegisterRequest, DeviceRegisterResponse
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings


def authenticate_user(db: Session, req: LoginRequest) -> LoginResponse:
    user = db.query(User).filter(
        User.school_id == req.school_id,
        User.username == req.username,
        User.deleted_at.is_(None)
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User account is {user.status}"
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token_payload = {
        "sub": user.id,
        "school_id": user.school_id,
        "username": user.username,
        "role": user.role,
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserSummary(
            id=user.id,
            school_id=user.school_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
        )
    )


def refresh_user_token(db: Session, refresh_token_str: str) -> TokenRefreshResponse:
    payload = decode_token(refresh_token_str)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or valid"
        )

    token_payload = {
        "sub": user.id,
        "school_id": user.school_id,
        "username": user.username,
        "role": user.role,
    }
    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token(token_payload)

    return TokenRefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def register_device(db: Session, school_id: str, user_id: Optional[str], req: DeviceRegisterRequest) -> DeviceRegisterResponse:
    device = db.query(Device).filter(Device.id == req.device_id).first()
    now = datetime.now(timezone.utc)

    if device:
        if device.status == "revoked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="DEVICE_REVOKED: This device has been revoked and cannot be registered"
            )
        device.device_name = req.device_name
        device.platform = req.platform
        device.app_version = req.app_version
        device.protocol_version = req.protocol_version
        device.credential_hash = req.credential_hash
        device.last_seen_at = now
        if user_id:
            device.user_id = user_id
    else:
        device = Device(
            id=req.device_id,
            school_id=school_id,
            user_id=user_id,
            device_name=req.device_name,
            platform=req.platform,
            app_version=req.app_version,
            protocol_version=req.protocol_version,
            credential_hash=req.credential_hash,
            status="active",
            registered_at=now,
            last_seen_at=now
        )
        db.add(device)

    # Ensure device sync state exists
    sync_state = db.query(DeviceSyncState).filter(DeviceSyncState.device_id == req.device_id).first()
    if not sync_state:
        sync_state = DeviceSyncState(
            school_id=school_id,
            device_id=req.device_id,
            last_received_sequence=0,
            status="active",
            last_sync_at=now
        )
        db.add(sync_state)

    db.commit()
    db.refresh(device)

    return DeviceRegisterResponse(
        device_id=device.id,
        status=device.status,
        registered_at=device.registered_at
    )
