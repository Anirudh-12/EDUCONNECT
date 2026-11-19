from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.identity import User
from app.modules.classroom.schemas import ClassroomCreate, ClassroomResponse, MembershipCreate, MembershipResponse
from app.modules.classroom import service

classroom_router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@classroom_router.get("", response_model=List[ClassroomResponse], summary="List Classrooms")
def list_classrooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return service.list_classrooms(db, current_user.school_id)


@classroom_router.post("", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED, summary="Create Classroom")
def create_classroom(
    data: ClassroomCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db)
):
    return service.create_classroom(db, current_user.school_id, data)


@classroom_router.post("/{classroom_id}/memberships", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED, summary="Add Member to Classroom")
def add_membership(
    classroom_id: str,
    data: MembershipCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db)
):
    return service.add_membership(db, current_user.school_id, classroom_id, data)
