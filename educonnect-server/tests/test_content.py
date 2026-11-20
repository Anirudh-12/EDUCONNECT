import hashlib
import io


def _get_auth_token(client, username="student1", password="learn123"):
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "school_id": "0194c7b0-0000-7000-8000-000000000001",
            "username": username,
            "password": password,
        },
    )
    return login_res.json()["access_token"]


def test_content_manifest(client):
    token = _get_auth_token(client)
    res = client.get(
        "/api/v1/content/manifest", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "school_id" in data
    assert "generated_at" in data
    assert "items" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "content_id" in item
    assert "version_id" in item
    assert "sha256" in item
    assert len(item["sha256"]) == 64
    assert item["size_bytes"] > 0
    assert "download_path" in item


def test_content_download_full(client):
    token = _get_auth_token(client)
    content_id = "0194c7b0-5000-7000-8000-000000000001"
    res = client.get(
        f"/api/v1/content/{content_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert "X-Content-SHA256" in res.headers
    assert res.headers["Accept-Ranges"] == "bytes"

    server_sha = res.headers["X-Content-SHA256"]
    body = res.content
    computed_sha = hashlib.sha256(body).hexdigest()
    assert computed_sha == server_sha
    assert len(body) == int(res.headers["Content-Length"])


def test_content_download_range_bytes(client):
    token = _get_auth_token(client)
    content_id = "0194c7b0-5000-7000-8000-000000000001"

    # 1. Fetch full size first
    full_res = client.get(
        f"/api/v1/content/{content_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    total_len = len(full_res.content)
    assert total_len > 10

    # 2. Request first 10 bytes: 0-9
    res_range1 = client.get(
        f"/api/v1/content/{content_id}/download",
        headers={"Authorization": f"Bearer {token}", "Range": "bytes=0-9"},
    )
    assert res_range1.status_code == 206
    assert res_range1.headers["Content-Range"] == f"bytes 0-9/{total_len}"
    assert len(res_range1.content) == 10
    assert res_range1.content == full_res.content[:10]

    # 3. Request remainder from byte 10 onwards
    res_range2 = client.get(
        f"/api/v1/content/{content_id}/download",
        headers={
            "Authorization": f"Bearer {token}",
            "Range": f"bytes=10-{total_len - 1}",
        },
    )
    assert res_range2.status_code == 206
    assert (
        res_range2.headers["Content-Range"] == f"bytes 10-{total_len - 1}/{total_len}"
    )
    assert len(res_range2.content) == (total_len - 10)
    assert res_range2.content == full_res.content[10:]

    # 4. Concatenating both parts reproduces the exact original file
    reconstructed = res_range1.content + res_range2.content
    assert reconstructed == full_res.content
    assert (
        hashlib.sha256(reconstructed).hexdigest()
        == res_range1.headers["X-Content-SHA256"]
    )


def test_content_download_invalid_range(client):
    token = _get_auth_token(client)
    content_id = "0194c7b0-5000-7000-8000-000000000001"
    res = client.get(
        f"/api/v1/content/{content_id}/download",
        headers={"Authorization": f"Bearer {token}", "Range": "bytes=999999-9999999"},
    )
    assert res.status_code == 416
    assert "Content-Range" in res.headers


def test_content_upload(client):
    # Student role cannot upload
    student_token = _get_auth_token(client, username="student1", password="learn123")
    fake_file = io.BytesIO(b"Sample PDF content for testing uploads")
    res_forbidden = client.post(
        "/api/v1/content/upload",
        headers={"Authorization": f"Bearer {student_token}"},
        files={"file": ("test.pdf", fake_file, "application/pdf")},
        data={"title": "Test Upload", "content_type": "pdf"},
    )
    assert res_forbidden.status_code == 403

    # Teacher role can upload
    teacher_token = _get_auth_token(client, username="teacher1", password="teach123")
    fake_file = io.BytesIO(b"Sample PDF content for testing teacher uploads")
    expected_sha = hashlib.sha256(fake_file.getvalue()).hexdigest()

    res_ok = client.post(
        "/api/v1/content/upload",
        headers={"Authorization": f"Bearer {teacher_token}"},
        files={"file": ("teacher_test.pdf", fake_file, "application/pdf")},
        data={"title": "Teacher Upload Doc", "content_type": "pdf"},
    )
    assert res_ok.status_code == 201
    data = res_ok.json()
    assert data["sha256"] == expected_sha
    assert "content_id" in data
    assert "download_path" in data
