import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.core.database as core_db

# Create isolated in-memory SQLite engine for tests with foreign keys enabled
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Monkey-patch database engine and SessionLocal so all application code uses test_engine
core_db.engine = test_engine
core_db.SessionLocal = TestSessionLocal

from app.core.database import get_db, init_db
from app.db.seed import seed_data
from app.main import app
from app.models.assessment import Answer, AssessmentAttempt
from app.models.learning import LearningEvent, LessonProgress, StudentNote
from app.models.sync import DeviceSyncState, SyncEventInbox


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db()
    seed_data()


@pytest.fixture(autouse=True)
def clean_transient_records():
    db = TestSessionLocal()
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
