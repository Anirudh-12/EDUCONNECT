def test_login_success(client):
    school_id = "0194c7b0-0000-7000-8000-000000000001"

    # Test admin login
    res = client.post(
        "/api/v1/auth/login",
        json={"school_id": school_id, "username": "admin", "password": "admin123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"

    # Test student login
    res_student = client.post(
        "/api/v1/auth/login",
        json={"school_id": school_id, "username": "student1", "password": "learn123"},
    )
    assert res_student.status_code == 200
    data_student = res_student.json()
    assert data_student["user"]["username"] == "student1"
    assert data_student["user"]["role"] == "student"


def test_login_invalid_password(client):
    res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "admin",
            "password": "wrongpassword",
        },
    )
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"


def test_login_invalid_user(client):
    res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "nonexistent_user",
            "password": "somepassword",
        },
    )
    assert res.status_code == 401
    data = res.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"


def test_token_refresh(client):
    # First login to obtain refresh token
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "teacher1",
            "password": "teach123",
        },
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    # Refresh
    refresh_res = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    ref_data = refresh_res.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data
    assert ref_data["token_type"] == "bearer"


def test_token_refresh_invalid(client):
    res = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid.jwt.token"}
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


def test_get_current_user_profile(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": "student1",
            "password": "learn123",
        },
    )
    token = login_res.json()["access_token"]
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "student1"
    assert data["role"] == "student"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
