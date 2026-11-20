from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.identity import User
from app.modules.classroom import service
from app.modules.classroom.schemas import (
    ClassroomCreate,
    ClassroomResponse,
    ClassroomUpdate,
    MembershipCreate,
    MembershipResponse,
)

classroom_router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@classroom_router.get(
    "", response_model=list[ClassroomResponse], summary="List Classrooms"
)
def list_classrooms(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.list_classrooms(db, current_user.school_id)


@classroom_router.get(
    "/{classroom_id}", response_model=ClassroomResponse, summary="Get Classroom Details"
)
def get_classroom(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.get_classroom(db, current_user.school_id, classroom_id)


@classroom_router.post(
    "",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Classroom",
)
def create_classroom(
    data: ClassroomCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.create_classroom(db, current_user.school_id, data)


@classroom_router.put(
    "/{classroom_id}", response_model=ClassroomResponse, summary="Update Classroom"
)
def update_classroom(
    classroom_id: str,
    data: ClassroomUpdate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.update_classroom(db, current_user.school_id, classroom_id, data)


@classroom_router.delete("/{classroom_id}", summary="Delete Classroom")
def delete_classroom(
    classroom_id: str,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.delete_classroom(db, current_user.school_id, classroom_id)


@classroom_router.get(
    "/{classroom_id}/memberships",
    response_model=list[MembershipResponse],
    summary="List Classroom Memberships",
)
def list_memberships(
    classroom_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_memberships(db, current_user.school_id, classroom_id)


@classroom_router.post(
    "/{classroom_id}/memberships",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Member to Classroom",
)
def add_membership(
    classroom_id: str,
    data: MembershipCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.add_membership(db, current_user.school_id, classroom_id, data)


@classroom_router.delete(
    "/{classroom_id}/memberships/{membership_id}",
    summary="Remove Member from Classroom",
)
def remove_membership(
    classroom_id: str,
    membership_id: str,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: Session = Depends(get_db),
):
    return service.remove_membership(
        db, current_user.school_id, classroom_id, membership_id
    )
