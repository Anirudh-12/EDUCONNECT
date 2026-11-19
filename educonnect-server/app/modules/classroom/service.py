from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.classroom import Classroom, ClassroomMembership
from app.modules.classroom.schemas import ClassroomCreate, ClassroomResponse, MembershipCreate, MembershipResponse


def list_classrooms(db: Session, school_id: str) -> List[ClassroomResponse]:
    rooms = db.query(Classroom).filter(Classroom.school_id == school_id).all()
    return [ClassroomResponse.model_validate(r) for r in rooms]


def create_classroom(db: Session, school_id: str, data: ClassroomCreate) -> ClassroomResponse:
    room = Classroom(
        school_id=school_id,
        name=data.name,
        grade_level=data.grade_level,
        section=data.section,
        academic_year=data.academic_year,
        status="active"
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return ClassroomResponse.model_validate(room)


def add_membership(db: Session, school_id: str, classroom_id: str, data: MembershipCreate) -> MembershipResponse:
    room = db.query(Classroom).filter(Classroom.id == classroom_id, Classroom.school_id == school_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    existing = db.query(ClassroomMembership).filter(
        ClassroomMembership.classroom_id == classroom_id,
        ClassroomMembership.user_id == data.user_id
    ).first()
    if existing:
        return MembershipResponse.model_validate(existing)

    membership = ClassroomMembership(
        school_id=school_id,
        classroom_id=classroom_id,
        user_id=data.user_id,
        membership_role=data.membership_role
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return MembershipResponse.model_validate(membership)
