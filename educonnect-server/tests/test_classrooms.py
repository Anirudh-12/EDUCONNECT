def _get_admin_token(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "admin",
            "password": "admin123",
        },
    )
    return login_res.json()["access_token"]


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


def test_classroom_crud_lifecycle(client):
    admin_token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create classroom
    create_res = client.post(
        "/api/v1/classrooms",
        headers=headers,
        json={
            "name": "Grade 9-C",
            "grade_level": "9",
            "section": "C",
            "academic_year": "2026-2027",
        },
    )
    assert create_res.status_code == 201
    classroom_id = create_res.json()["id"]

    # 2. Get classroom details
    get_res = client.get(f"/api/v1/classrooms/{classroom_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Grade 9-C"

    # 3. Update classroom
    update_res = client.put(
        f"/api/v1/classrooms/{classroom_id}",
        headers=headers,
        json={"name": "Grade 9-C (Advanced)"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Grade 9-C (Advanced)"

    # 4. Add student membership
    student_id = "0194c7b0-1000-7000-8000-000000000001"
    add_mem_res = client.post(
        f"/api/v1/classrooms/{classroom_id}/memberships",
        headers=headers,
        json={"user_id": student_id, "membership_role": "student"},
    )
    assert add_mem_res.status_code == 201
    membership_id = add_mem_res.json()["id"]

    # 5. List memberships
    list_mem_res = client.get(
        f"/api/v1/classrooms/{classroom_id}/memberships", headers=headers
    )
    assert list_mem_res.status_code == 200
    assert len(list_mem_res.json()) >= 1

    # 6. Remove membership
    del_mem_res = client.delete(
        f"/api/v1/classrooms/{classroom_id}/memberships/{membership_id}",
        headers=headers,
    )
    assert del_mem_res.status_code == 200

    # 7. Delete classroom
    del_res = client.delete(f"/api/v1/classrooms/{classroom_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify not found
    get_deleted = client.get(f"/api/v1/classrooms/{classroom_id}", headers=headers)
    assert get_deleted.status_code == 404


def test_student_cannot_create_classroom(client):
    student_token = _get_student_token(client)
    res = client.post(
        "/api/v1/classrooms",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "name": "Unauthorized Class",
            "grade_level": "1",
            "academic_year": "2026-2027",
        },
    )
    assert res.status_code == 403
