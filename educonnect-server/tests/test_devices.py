import uuid


def test_device_registration_unauthenticated(client):
    res = client.post("/api/v1/devices/register", json={
        "device_id": str(uuid.uuid4()),
        "device_name": "Test Tablet",
        "platform": "Android",
        "app_version": "1.0.0",
        "protocol_version": 1,
        "credential_hash": "dummyhash"
    })
    assert res.status_code == 401


def test_device_registration_authenticated(client):
    # Login as student
    login_res = client.post("/api/v1/auth/login", json={
        "school_id": "0194c7b0-0000-7000-8000-000000000001",
        "username": "student1",
        "password": "learn123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    new_device_id = str(uuid.uuid4())
    res = client.post("/api/v1/devices/register", headers=headers, json={
        "device_id": new_device_id,
        "device_name": "Student Tablet B",
        "platform": "Android",
        "app_version": "1.0.0",
        "protocol_version": 1,
        "credential_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["device_id"] == new_device_id
    assert data["status"] == "active"
    assert "registered_at" in data

    # Re-registering existing device
    res_update = client.post("/api/v1/devices/register", headers=headers, json={
        "device_id": new_device_id,
        "device_name": "Student Tablet B (Renamed)",
        "platform": "Android",
        "app_version": "1.0.1",
        "protocol_version": 1,
        "credential_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    })
    assert res_update.status_code == 201
    assert res_update.json()["status"] == "active"
