import uuid
from datetime import datetime, timezone


def _get_student_token(client):
    login_res = client.post("/api/v1/auth/login", json={
        "school_id": "0194c7b0-0000-7000-8000-000000000001",
        "username": "student1",
        "password": "learn123"
    })
    return login_res.json()["access_token"]


def test_get_assessment_student_view(client):
    token = _get_student_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    assessment_id = "0194c7b0-9100-7000-8000-000000000001"

    res = client.get(f"/api/v1/assessments/{assessment_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == assessment_id
    assert data["title"] == "Fractions Quiz 1"
    assert len(data["questions"]) >= 1

    q = data["questions"][0]
    assert "question_text" in q
    assert "options_json" in q
    # Correct answer and explanation must NEVER be in student view
    assert "correct_answer_json" not in q
    assert "explanation" not in q


def test_submit_assessment_attempt(client):
    token = _get_student_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    assessment_id = "0194c7b0-9100-7000-8000-000000000001"
    question_id = "0194c7b0-9200-7000-8000-000000000001"

    attempt_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()

    submit_payload = {
        "attempt_id": attempt_id,
        "device_id": "0194c7b0-2000-7000-8000-000000000001",
        "started_at": now_str,
        "submitted_at": now_str,
        "answers": [
            {
                "question_id": question_id,
                "answer_json": "3/4"
            }
        ]
    }

    res = client.post(f"/api/v1/assessments/{assessment_id}/attempts", headers=headers, json=submit_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["attempt_id"] == attempt_id
    assert data["status"] == "graded"
    assert data["score"] == 10.0
    assert data["maximum_score"] == 10.0
    assert data["grading_status"] == "automatic"

    # Test idempotency: re-submit same attempt_id returns identical result
    res_dup = client.post(f"/api/v1/assessments/{assessment_id}/attempts", headers=headers, json=submit_payload)
    assert res_dup.status_code in (200, 201)
    data_dup = res_dup.json()
    assert data_dup["attempt_id"] == attempt_id
    assert data_dup["score"] == 10.0
