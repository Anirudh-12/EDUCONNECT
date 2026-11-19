import hashlib
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.school import School
from app.models.identity import User, Device
from app.models.classroom import Classroom, ClassroomMembership
from app.models.course import Course, CourseEnrollment, Lesson, LessonContent
from app.models.content import Content, ContentVersion
from app.models.assessment import Assessment, Question
from app.models.sync import DeviceSyncState, ServerChangeLog


def seed_data(db: Session = None):
    close_at_end = False
    if db is None:
        db = SessionLocal()
        close_at_end = True

    try:
        now = datetime.now(timezone.utc)
        school_id = settings.DEFAULT_SCHOOL_ID

        # 1. School
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            school = School(
                id=school_id,
                name="Local School Alpha",
                code="ALPHA01",
                address="District 1, Rural Region",
                timezone="UTC",
                preferred_language="en",
                settings_json={"offline_mode": True, "sync_enabled": True}
            )
            db.add(school)
            db.flush()

        # 2. Users
        # Admin
        admin_id = "0194c7b0-1000-7000-8000-000000000000"
        admin = db.query(User).filter(User.id == admin_id).first()
        if not admin:
            admin = User(
                id=admin_id,
                school_id=school_id,
                username="admin",
                email="admin@school.local",
                password_hash=hash_password("admin123"),
                first_name="System",
                last_name="Admin",
                role="admin",
                status="active"
            )
            db.add(admin)

        # Teacher
        teacher_id = "0194c7b0-1000-7000-8000-000000000002"
        teacher = db.query(User).filter(User.id == teacher_id).first()
        if not teacher:
            teacher = User(
                id=teacher_id,
                school_id=school_id,
                username="teacher1",
                email="teacher1@school.local",
                password_hash=hash_password("teach123"),
                first_name="Sarah",
                last_name="Connor",
                role="teacher",
                status="active"
            )
            db.add(teacher)

        # Student
        student_id = "0194c7b0-1000-7000-8000-000000000001"
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            student = User(
                id=student_id,
                school_id=school_id,
                username="student1",
                email=None,
                password_hash=hash_password("learn123"),
                first_name="Jane",
                last_name="Doe",
                role="student",
                status="active"
            )
            db.add(student)

        db.flush()

        # 3. Device
        device_id = "0194c7b0-2000-7000-8000-000000000001"
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            device = Device(
                id=device_id,
                school_id=school_id,
                user_id=student_id,
                device_name="Galaxy Tab A9 (Lab 1)",
                platform="Android",
                app_version="1.0.0",
                protocol_version=1,
                credential_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                status="active",
                registered_at=now,
                last_seen_at=now
            )
            db.add(device)

        sync_state = db.query(DeviceSyncState).filter(DeviceSyncState.device_id == device_id).first()
        if not sync_state:
            sync_state = DeviceSyncState(
                school_id=school_id,
                device_id=device_id,
                last_received_sequence=0,
                status="active",
                last_sync_at=now
            )
            db.add(sync_state)

        db.flush()

        # 4. Classroom
        classroom_id = "0194c7b0-2500-7000-8000-000000000001"
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            classroom = Classroom(
                id=classroom_id,
                school_id=school_id,
                name="Grade 7-A",
                grade_level="7",
                section="A",
                academic_year="2026-2027",
                status="active"
            )
            db.add(classroom)
            db.flush()

            # Memberships
            db.add(ClassroomMembership(
                school_id=school_id,
                classroom_id=classroom_id,
                user_id=teacher_id,
                membership_role="teacher"
            ))
            db.add(ClassroomMembership(
                school_id=school_id,
                classroom_id=classroom_id,
                user_id=student_id,
                membership_role="student"
            ))

        # 5. Content file on disk
        storage_dir = settings.CONTENT_STORAGE_DIR
        storage_dir.mkdir(parents=True, exist_ok=True)
        sample_file = storage_dir / "fractions-chapter-1.pdf"
        sample_content_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Fractions Chapter 1) /Author (EduConnect) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        sample_file.write_bytes(sample_content_bytes)
        file_sha256 = hashlib.sha256(sample_content_bytes).hexdigest()
        file_size = len(sample_content_bytes)

        content_id = "0194c7b0-5000-7000-8000-000000000001"
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            content = Content(
                id=content_id,
                school_id=school_id,
                title="Fractions Chapter 1 PDF",
                description="Introductory lesson on fractions and decimals",
                content_type="pdf",
                mime_type="application/pdf",
                language="en",
                subject="Mathematics",
                grade_level="7",
                status="published",
                created_by=teacher_id
            )
            db.add(content)
            db.flush()

        version_id = "0194c7b0-5100-7000-8000-000000000001"
        version = db.query(ContentVersion).filter(ContentVersion.id == version_id).first()
        if not version:
            version = ContentVersion(
                id=version_id,
                school_id=school_id,
                content_id=content_id,
                version_number=1,
                sha256=file_sha256,
                storage_path=str(sample_file),
                file_size_bytes=file_size,
                mime_type="application/pdf",
                published_at=now
            )
            db.add(version)

        # 6. Course & Lesson
        course_id = "0194c7b0-3000-7000-8000-000000000001"
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            course = Course(
                id=course_id,
                school_id=school_id,
                title="Mathematics Grade 7",
                description="Fractions, Decimals, and Basic Geometry",
                subject="Mathematics",
                grade_level="7",
                language="en",
                thumbnail_content_id=content_id,
                status="published",
                created_by=teacher_id,
                published_at=now
            )
            db.add(course)
            db.flush()

            # Course Enrollment
            db.add(CourseEnrollment(
                school_id=school_id,
                course_id=course_id,
                user_id=student_id,
                status="active"
            ))

        lesson_id = "0194c7b0-3100-7000-8000-000000000001"
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            lesson = Lesson(
                id=lesson_id,
                school_id=school_id,
                course_id=course_id,
                title="1. Introduction to Fractions",
                description="Understanding numerators and denominators",
                lesson_type="document",
                sequence_number=1,
                estimated_duration=1800,
                status="published"
            )
            db.add(lesson)
            db.flush()

            # Lesson Content Mapping
            db.add(LessonContent(
                school_id=school_id,
                lesson_id=lesson_id,
                content_id=content_id,
                sequence_number=1,
                is_required=True
            ))

        # 7. Assessment
        assessment_id = "0194c7b0-9100-7000-8000-000000000001"
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            assessment = Assessment(
                id=assessment_id,
                school_id=school_id,
                course_id=course_id,
                title="Fractions Quiz 1",
                description="Basic diagnostic quiz on fraction addition",
                assessment_type="quiz",
                total_marks=10.0,
                passing_marks=6.0,
                time_limit_seconds=900,
                attempts_allowed=2,
                status="published",
                created_by=teacher_id
            )
            db.add(assessment)
            db.flush()

            question_id = "0194c7b0-9200-7000-8000-000000000001"
            question = Question(
                id=question_id,
                school_id=school_id,
                assessment_id=assessment_id,
                question_type="mcq",
                question_text="What is 1/2 + 1/4?",
                options_json=["1/2", "3/4", "2/6", "1"],
                correct_answer_json="3/4",
                marks=10.0,
                sequence_number=1,
                explanation="1/2 is equivalent to 2/4. 2/4 + 1/4 = 3/4."
            )
            db.add(question)

        # 8. Initial Server Change Log Entry
        log = db.query(ServerChangeLog).filter(ServerChangeLog.entity_id == course_id).first()
        if not log:
            db.add(ServerChangeLog(
                school_id=school_id,
                entity_type="course",
                entity_id=course_id,
                change_type="created",
                version=1
            ))

        db.commit()
        print("Database seeded successfully with default school, users, courses, content, and assessments.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if close_at_end:
            db.close()


if __name__ == "__main__":
    init_db()
    seed_data()
