def _get_student_token(client):
    login_res = client.post("/api/v1/auth/login", json={
        "school_id": "0194c7b0-0000-7000-8000-000000000001",
        "username": "student1",
        "password": "learn123"
    })
    return login_res.json()["access_token"]


def test_list_courses(client):
    token = _get_student_token(client)
    res = client.get("/api/v1/courses", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 1
    course = data["items"][0]
    assert course["title"] == "Mathematics Grade 7"
    assert course["subject"] == "Mathematics"
    assert course["grade_level"] == "7"
    assert course["lessons_count"] >= 1


def test_get_course_details(client):
    token = _get_student_token(client)
    course_id = "0194c7b0-3000-7000-8000-000000000001"
    res = client.get(f"/api/v1/courses/{course_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == course_id
    assert data["title"] == "Mathematics Grade 7"


def test_get_course_not_found(client):
    token = _get_student_token(client)
    res = client.get("/api/v1/courses/0194c7b0-9999-7000-8000-000000000000", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_course_lessons(client):
    token = _get_student_token(client)
    course_id = "0194c7b0-3000-7000-8000-000000000001"
    res = client.get(f"/api/v1/courses/{course_id}/lessons", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["course_id"] == course_id
    assert len(data["lessons"]) >= 1

    lesson = data["lessons"][0]
    assert lesson["title"] == "1. Introduction to Fractions"
    assert len(lesson["contents"]) >= 1
    content_item = lesson["contents"][0]
    assert "content_id" in content_item
    assert "sha256" in content_item
    assert len(content_item["sha256"]) == 64
    assert content_item["mime_type"] == "application/pdf"
