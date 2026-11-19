import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, init_db
from app.db.seed import seed_data
from app.models.learning import LessonProgress, LearningEvent, StudentNote
from app.models.sync import SyncEventInbox, DeviceSyncState
from app.models.assessment import AssessmentAttempt, Answer


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()
    seed_data()


@pytest.fixture(autouse=True)
def clean_transient_records():
    db = SessionLocal()
    try:
        db.query(Answer).delete()
        db.query(AssessmentAttempt).delete()
        db.query(SyncEventInbox).delete()
        db.query(LearningEvent).delete()
        db.query(LessonProgress).delete()
        db.query(StudentNote).delete()
        # Reset device sync sequence
        sync_states = db.query(DeviceSyncState).all()
        for s in sync_states:
            s.last_received_sequence = 0
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
