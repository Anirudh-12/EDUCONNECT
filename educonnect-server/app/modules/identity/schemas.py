from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserSummary(BaseModel):
    id: str
    school_id: str
    username: str
    first_name: str
    last_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    school_id: str
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str
    platform: str = "Android"
    app_version: str
    protocol_version: int = 1
    credential_hash: str


class DeviceRegisterResponse(BaseModel):
    device_id: str
    status: str
    registered_at: datetime
