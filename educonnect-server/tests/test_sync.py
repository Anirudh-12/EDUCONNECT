import uuid
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.learning import LessonProgress
from app.models.sync import SyncEventInbox


def _get_student_token(client):
    login_res = client.post("/api/v1/auth/login", json={
        "school_id": "0194c7b0-0000-7000-8000-000000000001",
        "username": "student1",
        "password": "learn123"
    })
    return login_res.json()["access_token"]


def test_sync_batch_ingestion(client):
    token = _get_student_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Device-ID": "0194c7b0-2000-7000-8000-000000000001"}

    event_id1 = str(uuid.uuid4())
    event_id2 = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())
    lesson_id = "0194c7b0-3100-7000-8000-000000000001"
    now_str = datetime.now(timezone.utc).isoformat()

    batch_payload = {
        "protocol_version": 1,
        "device_id": "0194c7b0-2000-7000-8000-000000000001",
        "batch_id": batch_id,
        "events": [
            {
                "event_id": event_id1,
                "event_type": "lesson.started",
                "schema_version": 1,
                "school_id": "0194c7b0-0000-7000-8000-000000000001",
                "user_id": "0194c7b0-1000-7000-8000-000000000001",
                "device_id": "0194c7b0-2000-7000-8000-000000000001",
                "entity_type": "lesson",
                "entity_id": lesson_id,
                "device_sequence": 1,
                "occurred_at": now_str,
                "recorded_at": now_str,
                "payload": {"course_id": "0194c7b0-3000-7000-8000-000000000001"}
            },
            {
                "event_id": event_id2,
                "event_type": "lesson.progress_updated",
                "schema_version": 1,
                "school_id": "0194c7b0-0000-7000-8000-000000000001",
                "user_id": "0194c7b0-1000-7000-8000-000000000001",
                "device_id": "0194c7b0-2000-7000-8000-000000000001",
                "entity_type": "lesson",
                "entity_id": lesson_id,
                "device_sequence": 2,
                "occurred_at": now_str,
                "recorded_at": now_str,
                "payload": {"course_id": "0194c7b0-3000-7000-8000-000000000001", "completion_percentage": 60, "last_position_seconds": 300}
            }
        ]
    }

    res = client.post("/api/v1/sync/v1/events", headers=headers, json=batch_payload)
    assert res.status_code == 200
    data = res.json()
    assert event_id1 in data["acknowledged"]
    assert event_id2 in data["acknowledged"]
    assert len(data["duplicates"]) == 0
    assert "server_cursor" in data

    # Verify database projection
    db = SessionLocal()
    progress = db.query(LessonProgress).filter(
        LessonProgress.user_id == "0194c7b0-1000-7000-8000-000000000001",
        LessonProgress.lesson_id == lesson_id
    ).first()
    assert progress is not None
    assert progress.status == "in_progress"
    assert progress.completion_percentage == 60.0
    assert progress.last_position_seconds == 300
    db.close()


def test_sync_idempotency_duplicate_submission(client):
    token = _get_student_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Device-ID": "0194c7b0-2000-7000-8000-000000000001"}

    event_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()

    batch_payload = {
        "protocol_version": 1,
        "device_id": "0194c7b0-2000-7000-8000-000000000001",
        "batch_id": batch_id,
        "events": [
            {
                "event_id": event_id,
                "event_type": "note.created",
                "schema_version": 1,
                "school_id": "0194c7b0-0000-7000-8000-000000000001",
                "user_id": "0194c7b0-1000-7000-8000-000000000001",
                "device_id": "0194c7b0-2000-7000-8000-000000000001",
                "entity_type": "note",
                "entity_id": "0194c7b0-3100-7000-8000-000000000001",
                "device_sequence": 10,
                "occurred_at": now_str,
                "recorded_at": now_str,
                "payload": {"content": "Fractions require common denominators before adding."}
            }
        ]
    }

    # 1. First submission -> acknowledged
    res1 = client.post("/api/v1/sync/v1/events", headers=headers, json=batch_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert event_id in data1["acknowledged"]
    assert event_id not in data1["duplicates"]

    # 2. Second submission (duplicate) -> recognized in duplicates list
    res2 = client.post("/api/v1/sync/v1/events", headers=headers, json=batch_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert event_id in data2["duplicates"]
    assert event_id not in data2["acknowledged"]

    # Verify sync_event_inbox has only 1 entry for this event_id
    db = SessionLocal()
    count = db.query(SyncEventInbox).filter(
        SyncEventInbox.school_id == "0194c7b0-0000-7000-8000-000000000001",
        SyncEventInbox.event_id == event_id
    ).count()
    assert count == 1
    db.close()


def test_sync_monotonic_progress(client):
    token = _get_student_token(client)
    headers = {"Authorization": f"Bearer {token}", "X-Device-ID": "0194c7b0-2000-7000-8000-000000000001"}

    lesson_id = "0194c7b0-3100-7000-8000-000000000001"
    now_str = datetime.now(timezone.utc).isoformat()

    # Step 1: Update progress to 80%
    ev1_id = str(uuid.uuid4())
    res1 = client.post("/api/v1/sync/v1/events", headers=headers, json={
        "protocol_version": 1,
        "device_id": "0194c7b0-2000-7000-8000-000000000001",
        "batch_id": str(uuid.uuid4()),
        "events": [{
            "event_id": ev1_id,
            "event_type": "lesson.progress_updated",
            "schema_version": 1,
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "user_id": "0194c7b0-1000-7000-8000-000000000001",
            "device_id": "0194c7b0-2000-7000-8000-000000000001",
            "entity_type": "lesson",
            "entity_id": lesson_id,
            "device_sequence": 20,
            "occurred_at": now_str,
            "recorded_at": now_str,
            "payload": {"completion_percentage": 80.0, "last_position_seconds": 500}
        }]
    })
    assert res1.status_code == 200

    # Step 2: Try to send an older event claiming 40%
    ev2_id = str(uuid.uuid4())
    res2 = client.post("/api/v1/sync/v1/events", headers=headers, json={
        "protocol_version": 1,
        "device_id": "0194c7b0-2000-7000-8000-000000000001",
        "batch_id": str(uuid.uuid4()),
        "events": [{
            "event_id": ev2_id,
            "event_type": "lesson.progress_updated",
            "schema_version": 1,
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "user_id": "0194c7b0-1000-7000-8000-000000000001",
            "device_id": "0194c7b0-2000-7000-8000-000000000001",
            "entity_type": "lesson",
            "entity_id": lesson_id,
            "device_sequence": 21,
            "occurred_at": now_str,
            "recorded_at": now_str,
            "payload": {"completion_percentage": 40.0, "last_position_seconds": 200}
        }]
    })
    assert res2.status_code == 200

    # Verify progress remained at 80% (monotonic progress)
    db = SessionLocal()
    progress = db.query(LessonProgress).filter(
        LessonProgress.user_id == "0194c7b0-1000-7000-8000-000000000001",
        LessonProgress.lesson_id == lesson_id
    ).first()
    assert progress.completion_percentage == 80.0
    db.close()

    # Step 3: Complete lesson
    ev3_id = str(uuid.uuid4())
    res3 = client.post("/api/v1/sync/v1/events", headers=headers, json={
        "protocol_version": 1,
        "device_id": "0194c7b0-2000-7000-8000-000000000001",
        "batch_id": str(uuid.uuid4()),
        "events": [{
            "event_id": ev3_id,
            "event_type": "lesson.completed",
            "schema_version": 1,
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "user_id": "0194c7b0-1000-7000-8000-000000000001",
            "device_id": "0194c7b0-2000-7000-8000-000000000001",
            "entity_type": "lesson",
            "entity_id": lesson_id,
            "device_sequence": 22,
            "occurred_at": now_str,
            "recorded_at": now_str,
            "payload": {"completion_percentage": 100.0}
        }]
    })
    assert res3.status_code == 200

    db = SessionLocal()
    progress = db.query(LessonProgress).filter(
        LessonProgress.user_id == "0194c7b0-1000-7000-8000-000000000001",
        LessonProgress.lesson_id == lesson_id
    ).first()
    assert progress.status == "completed"
    assert progress.completion_percentage == 100.0
    assert progress.completed_at is not None
    db.close()


def test_sync_status_and_changes(client):
    token = _get_student_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Status
    res_status = client.get(
        "/api/v1/sync/v1/status?device_id=0194c7b0-2000-7000-8000-000000000001",
        headers=headers
    )
    assert res_status.status_code == 200
    st_data = res_status.json()
    assert st_data["protocol_version"] == 1
    assert "server_time" in st_data
    assert "server_cursor" in st_data

    # Changes
    res_changes = client.get(
        f"/api/v1/sync/v1/changes?cursor={st_data['server_cursor']}",
        headers=headers
    )
    assert res_changes.status_code == 200
    ch_data = res_changes.json()
    assert "server_cursor" in ch_data
    assert "changes" in ch_data
    assert isinstance(ch_data["changes"], list)


def test_sync_revoked_device_rejected(client):
    from app.models.identity import Device

    token = _get_student_token(client)
    db = SessionLocal()
    revoked_id = str(uuid.uuid4())
    revoked_device = Device(
        id=revoked_id,
        school_id="0194c7b0-0000-7000-8000-000000000001",
        user_id="0194c7b0-1000-7000-8000-000000000001",
        device_name="Revoked Device",
        platform="Android",
        app_version="1.0.0",
        protocol_version=1,
        credential_hash="somehash",
        status="revoked"
    )
    db.add(revoked_device)
    db.commit()
    db.close()

    headers = {"Authorization": f"Bearer {token}", "X-Device-ID": revoked_id}
    now_str = datetime.now(timezone.utc).isoformat()
    res = client.post("/api/v1/sync/v1/events", headers=headers, json={
        "protocol_version": 1,
        "device_id": revoked_id,
        "batch_id": str(uuid.uuid4()),
        "events": [{
            "event_id": str(uuid.uuid4()),
            "event_type": "lesson.started",
            "schema_version": 1,
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "user_id": "0194c7b0-1000-7000-8000-000000000001",
            "device_id": revoked_id,
            "entity_type": "lesson",
            "entity_id": "0194c7b0-3100-7000-8000-000000000001",
            "device_sequence": 1,
            "occurred_at": now_str,
            "recorded_at": now_str,
            "payload": {}
        }]
    })
    assert res.status_code == 403
    assert "DEVICE_REVOKED" in res.json()["error"]["code"]

