from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classroom import Classroom, ClassroomMembership
from app.models.sync import ServerChangeLog
from app.modules.classroom.schemas import (
    ClassroomCreate,
    ClassroomResponse,
    ClassroomUpdate,
    MembershipCreate,
    MembershipResponse,
)


def list_classrooms(db: Session, school_id: str) -> list[ClassroomResponse]:
    rooms = (
        db.execute(select(Classroom).where(Classroom.school_id == school_id))
        .scalars()
        .all()
    )
    return [ClassroomResponse.model_validate(r) for r in rooms]


def get_classroom(db: Session, school_id: str, classroom_id: str) -> ClassroomResponse:
    room = db.execute(
        select(Classroom).where(
            Classroom.id == classroom_id, Classroom.school_id == school_id
        )
    ).scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Classroom not found",
        )
    return ClassroomResponse.model_validate(room)


def update_classroom(
    db: Session, school_id: str, classroom_id: str, data: ClassroomUpdate
) -> ClassroomResponse:
    room = db.execute(
        select(Classroom).where(
            Classroom.id == classroom_id, Classroom.school_id == school_id
        )
    ).scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Classroom not found",
        )
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(room, field, val)
    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="classroom",
            entity_id=room.id,
            change_type="updated",
            version=2,
        )
    )
    db.commit()
    db.refresh(room)
    return ClassroomResponse.model_validate(room)


def delete_classroom(db: Session, school_id: str, classroom_id: str) -> dict:
    room = db.execute(
        select(Classroom).where(
            Classroom.id == classroom_id, Classroom.school_id == school_id
        )
    ).scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Classroom not found",
        )
    db.delete(room)
    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="classroom",
            entity_id=classroom_id,
            change_type="deleted",
            version=3,
        )
    )
    db.commit()
    return {"detail": "Classroom deleted successfully"}


def list_memberships(
    db: Session, school_id: str, classroom_id: str
) -> list[MembershipResponse]:
    room = db.execute(
        select(Classroom).where(
            Classroom.id == classroom_id, Classroom.school_id == school_id
        )
    ).scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Classroom not found",
        )
    memberships = (
        db.execute(
            select(ClassroomMembership).where(
                ClassroomMembership.classroom_id == classroom_id
            )
        )
        .scalars()
        .all()
    )
    return [MembershipResponse.model_validate(m) for m in memberships]


def remove_membership(
    db: Session, school_id: str, classroom_id: str, membership_id: str
) -> dict:
    m = db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.id == membership_id,
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.school_id == school_id,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RESOURCE_NOT_FOUND: Membership not found",
        )
    db.delete(m)
    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="classroom_membership",
            entity_id=membership_id,
            change_type="deleted",
            version=3,
        )
    )
    db.commit()
    return {"detail": "Membership removed successfully"}


def create_classroom(
    db: Session, school_id: str, data: ClassroomCreate
) -> ClassroomResponse:
    room = Classroom(
        school_id=school_id,
        name=data.name,
        grade_level=data.grade_level,
        section=data.section,
        academic_year=data.academic_year,
        status="active",
    )
    db.add(room)
    db.flush()

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="classroom",
            entity_id=room.id,
            change_type="created",
            version=1,
        )
    )
    db.commit()
    db.refresh(room)
    return ClassroomResponse.model_validate(room)


def add_membership(
    db: Session, school_id: str, classroom_id: str, data: MembershipCreate
) -> MembershipResponse:
    room = db.execute(
        select(Classroom).where(
            Classroom.id == classroom_id, Classroom.school_id == school_id
        )
    ).scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        )

    existing = db.execute(
        select(ClassroomMembership).where(
            ClassroomMembership.classroom_id == classroom_id,
            ClassroomMembership.user_id == data.user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return MembershipResponse.model_validate(existing)

    membership = ClassroomMembership(
        school_id=school_id,
        classroom_id=classroom_id,
        user_id=data.user_id,
        membership_role=data.membership_role,
    )
    db.add(membership)
    db.flush()

    db.add(
        ServerChangeLog(
            school_id=school_id,
            entity_type="classroom_membership",
            entity_id=membership.id,
            change_type="created",
            version=1,
        )
    )
    db.commit()
    db.refresh(membership)
    return MembershipResponse.model_validate(membership)
