from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.identity import User
from app.modules.identity.schemas import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
)
from app.modules.identity import service

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
device_router = APIRouter(prefix="/devices", tags=["Devices"])


@auth_router.post("/login", response_model=LoginResponse, summary="User Login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    return service.authenticate_user(db, req)


@auth_router.post("/refresh", response_model=TokenRefreshResponse, summary="Token Refresh")
def refresh_token(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    return service.refresh_user_token(db, req.refresh_token)


@device_router.post("/register", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED, summary="Device Registration")
def register_device(
    req: DeviceRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return service.register_device(db, current_user.school_id, current_user.id, req)
