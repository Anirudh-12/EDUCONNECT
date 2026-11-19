from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ClassroomCreate(BaseModel):
    name: str
    grade_level: str
    section: Optional[str] = None
    academic_year: str


class ClassroomResponse(BaseModel):
    id: str
    school_id: str
    name: str
    grade_level: str
    section: Optional[str] = None
    academic_year: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MembershipCreate(BaseModel):
    user_id: str
    membership_role: str  # student, teacher


class MembershipResponse(BaseModel):
    id: str
    school_id: str
    classroom_id: str
    user_id: str
    membership_role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
