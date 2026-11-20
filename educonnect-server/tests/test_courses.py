def _get_student_token(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "student1",
            "password": "learn123",
        },
    )
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
    res = client.get(
        f"/api/v1/courses/{course_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == course_id
    assert data["title"] == "Mathematics Grade 7"


def test_get_course_not_found(client):
    token = _get_student_token(client)
    res = client.get(
        "/api/v1/courses/0194c7b0-9999-7000-8000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_get_course_lessons(client):
    token = _get_student_token(client)
    course_id = "0194c7b0-3000-7000-8000-000000000001"
    res = client.get(
        f"/api/v1/courses/{course_id}/lessons",
        headers={"Authorization": f"Bearer {token}"},
    )
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


def _get_teacher_token(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "teacher1",
            "password": "teach123",
        },
    )
    return login_res.json()["access_token"]


def test_course_and_lesson_authoring_lifecycle(client):
    teacher_token = _get_teacher_token(client)
    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Create course
    create_course_res = client.post(
        "/api/v1/courses",
        headers=headers,
        json={
            "title": "Science Grade 7",
            "description": "Introductory Science",
            "subject": "Science",
            "grade_level": "7",
            "language": "en",
            "status": "published",
        },
    )
    assert create_course_res.status_code == 201
    course_id = create_course_res.json()["id"]

    # 2. Update course
    update_course_res = client.put(
        f"/api/v1/courses/{course_id}",
        headers=headers,
        json={"title": "General Science Grade 7"},
    )
    assert update_course_res.status_code == 200
    assert update_course_res.json()["title"] == "General Science Grade 7"

    # 3. Create lesson
    create_lesson_res = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=headers,
        json={
            "title": "1. Introduction to Cells",
            "description": "Cell structure and function",
            "lesson_type": "document",
            "sequence_number": 1,
            "estimated_duration": 1200,
        },
    )
    assert create_lesson_res.status_code == 201
    lesson_id = create_lesson_res.json()["id"]

    # 4. Update lesson
    update_lesson_res = client.put(
        f"/api/v1/courses/{course_id}/lessons/{lesson_id}",
        headers=headers,
        json={"title": "1. Cell Biology Foundations"},
    )
    assert update_lesson_res.status_code == 200
    assert update_lesson_res.json()["title"] == "1. Cell Biology Foundations"

    # 5. Add content to lesson
    content_id = "0194c7b0-5000-7000-8000-000000000001"
    add_content_res = client.post(
        f"/api/v1/courses/{course_id}/lessons/{lesson_id}/content",
        headers=headers,
        json={"content_id": content_id, "sequence_number": 1, "is_required": True},
    )
    assert add_content_res.status_code == 201
    assert add_content_res.json()["content_id"] == content_id

    # 6. Delete lesson
    del_lesson_res = client.delete(
        f"/api/v1/courses/{course_id}/lessons/{lesson_id}", headers=headers
    )
    assert del_lesson_res.status_code == 200

    # 7. Delete course
    del_course_res = client.delete(f"/api/v1/courses/{course_id}", headers=headers)
    assert del_course_res.status_code == 200

    # Verify course is not found
    get_res = client.get(f"/api/v1/courses/{course_id}", headers=headers)
    assert get_res.status_code == 404


def test_student_cannot_author_courses(client):
    student_token = _get_student_token(client)
    res = client.post(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Unauthorized Course",
            "subject": "Hacking",
            "grade_level": "10",
        },
    )
    assert res.status_code == 403
