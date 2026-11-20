from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClassroomCreate(BaseModel):
    name: str
    grade_level: str
    section: str | None = None
    academic_year: str


class ClassroomUpdate(BaseModel):
    name: str | None = None
    grade_level: str | None = None
    section: str | None = None
    academic_year: str | None = None
    status: str | None = None


class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[str] = None
    section: Optional[str] = None
    academic_year: Optional[str] = None
    status: Optional[str] = None


class ClassroomResponse(BaseModel):
    id: str
    school_id: str
    name: str
    grade_level: str
    section: str | None = None
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
