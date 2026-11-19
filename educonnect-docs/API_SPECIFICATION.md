# EDUCONNECT — API Specification

**Document:** API_SPECIFICATION.md  
**Version:** 1.0  
**Status:** Initial REST API baseline  
**Protocol:** HTTP/1.1 & HTTP/2 (TLS recommended for local school network)  
**Base Path:** `/api/v1`  
**Date:** 2026-11-19  

---

## 1. Overview & Conventions

This document specifies the REST API contract for the EDUCONNECT school server (`educonnect-server`). It serves as the authoritative interface definition for:
- Android student application (`educonnect-android`)
- Teacher and administrator web portal (`educonnect-admin`)
- Peer synchronization clients (`educonnect-sync`)

### 1.1 General Principles
- **Transport:** JSON (`application/json`) for request and response payloads, binary octet-stream for content files.
- **Identifiers:** Canonical UUIDv7 strings (e.g. `0194c7b0-1234-7000-8000-000000000001`).
- **Timestamps:** ISO 8601 strings in UTC format (e.g. `2026-11-19T12:30:00Z`).
- **Authentication:** Bearer tokens (JWT) in the `Authorization: Bearer <token>` header, supplemented by device credentials (`X-Device-ID`, `X-Device-Signature`).
- **Resumable Downloads:** Content binary downloads support HTTP standard `Range` and `If-Range` headers with SHA-256 integrity verification (`ETag` or `X-Content-SHA256`).

### 1.2 Standard Error Response Envelope

All error responses return standard HTTP status codes accompanied by the following JSON structure:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested course could not be found.",
    "details": {},
    "timestamp": "2026-11-19T12:30:00Z"
  }
}
```

Standard Error Codes:
- `UNAUTHENTICATED`: Missing, expired, or invalid credentials.
- `PERMISSION_DENIED`: User or device lacks necessary role/permission.
- `DEVICE_REVOKED`: Device registration has been invalidated or suspended.
- `RESOURCE_NOT_FOUND`: Target entity does not exist.
- `VALIDATION_FAILED`: Payload schema invalid or parameter constraint broken.
- `CONFLICT`: Unique constraint or state conflict.
- `RATE_LIMITED`: Request rate limit exceeded.
- `SERVER_ERROR`: Internal unhandled server error.

---

## 2. Authentication & Device Management

### 2.1 User Login
- **Endpoint:** `POST /api/v1/auth/login`
- **Auth:** Public
- **Description:** Authenticates student, teacher, or administrator with school credentials.

**Request Body:**
```json
{
  "school_id": "0194c7b0-0000-7000-8000-000000000001",
  "username": "student_jdoe",
  "password": "CleartextPasswordForHashVerification"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "0194c7b0-1000-7000-8000-000000000001",
    "school_id": "0194c7b0-0000-7000-8000-000000000001",
    "username": "student_jdoe",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "student"
  }
}
```

### 2.2 Token Refresh
- **Endpoint:** `POST /api/v1/auth/refresh`
- **Auth:** Public with Refresh Token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOi..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2.3 Device Registration
- **Endpoint:** `POST /api/v1/devices/register`
- **Auth:** Bearer Token required
- **Description:** Registers an Android device with the local school server.

**Request Body:**
```json
{
  "device_id": "0194c7b0-2000-7000-8000-000000000001",
  "device_name": "Galaxy Tab A9 (Lab 1)",
  "platform": "Android",
  "app_version": "1.0.0",
  "protocol_version": 1,
  "credential_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

**Response (201 Created):**
```json
{
  "device_id": "0194c7b0-2000-7000-8000-000000000001",
  "status": "active",
  "registered_at": "2026-11-19T12:00:00Z"
}
```

---

## 3. Classroom & Course Management

### 3.1 List Enrolled Courses
- **Endpoint:** `GET /api/v1/courses`
- **Auth:** Bearer Token
- **Query Params:** `status` (default: `published`)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "0194c7b0-3000-7000-8000-000000000001",
      "school_id": "0194c7b0-0000-7000-8000-000000000001",
      "title": "Mathematics Grade 7",
      "description": "Fractions, Decimals, and Basic Geometry",
      "subject": "Mathematics",
      "grade_level": "7",
      "language": "en",
      "thumbnail_content_id": "0194c7b0-4000-7000-8000-000000000001",
      "status": "published",
      "lessons_count": 12,
      "updated_at": "2026-11-19T10:00:00Z"
    }
  ],
  "total": 1
}
```

### 3.2 Get Course Details & Lessons
- **Endpoint:** `GET /api/v1/courses/{course_id}/lessons`
- **Auth:** Bearer Token

**Response (200 OK):**
```json
{
  "course_id": "0194c7b0-3000-7000-8000-000000000001",
  "lessons": [
    {
      "id": "0194c7b0-3100-7000-8000-000000000001",
      "title": "1. Introduction to Fractions",
      "description": "Understanding numerators and denominators",
      "lesson_type": "document",
      "sequence_number": 1,
      "estimated_duration": 1800,
      "contents": [
        {
          "content_id": "0194c7b0-5000-7000-8000-000000000001",
          "version_id": "0194c7b0-5100-7000-8000-000000000001",
          "title": "Fractions Chapter 1 PDF",
          "mime_type": "application/pdf",
          "file_size_bytes": 2048576,
          "sha256": "5f4dcc3b5aa765d61d8327deb882cf992b960bf746b19a0a55e2d6b38c20be84",
          "is_required": true
        }
      ]
    }
  ]
}
```

---

## 4. Content Storage & Verification

### 4.1 Get Content Manifest
- **Endpoint:** `GET /api/v1/content/manifest`
- **Auth:** Bearer Token
- **Description:** Returns the complete list of downloadable content versions with verification hashes.

**Response (200 OK):**
```json
{
  "school_id": "0194c7b0-0000-7000-8000-000000000001",
  "generated_at": "2026-11-19T12:00:00Z",
  "items": [
    {
      "content_id": "0194c7b0-5000-7000-8000-000000000001",
      "version_id": "0194c7b0-5100-7000-8000-000000000001",
      "filename": "fractions-chapter-1.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 2048576,
      "sha256": "5f4dcc3b5aa765d61d8327deb882cf992b960bf746b19a0a55e2d6b38c20be84",
      "download_path": "/api/v1/content/0194c7b0-5000-7000-8000-000000000001/download"
    }
  ]
}
```

### 4.2 Download Content Binary
- **Endpoint:** `GET /api/v1/content/{content_id}/download`
- **Headers:** Optional `Range: bytes=0-1048575`
- **Response:**
  - `200 OK` (Full binary stream)
  - `206 Partial Content` (Range slice)
  - Headers:
    - `Content-Type: application/pdf`
    - `Content-Length: <bytes>`
    - `Content-Range: bytes 0-1048575/2048576` (if range requested)
    - `ETag: "5f4dcc3b5aa765d61d8327deb882cf992b960bf746b19a0a55e2d6b38c20be84"`
    - `X-Content-SHA256: 5f4dcc3b5aa765d61d8327deb882cf992b960bf746b19a0a55e2d6b38c20be84`

---

## 5. Synchronization Endpoints (`/sync/v1/`)

### 5.1 Ingest Event Batch
- **Endpoint:** `POST /api/v1/sync/v1/events`
- **Auth:** Bearer Token + Device Headers (`X-Device-ID`)
- **Description:** Ingests an atomic batch of pending offline events. Guaranteed idempotent.

**Request Body:**
```json
{
  "protocol_version": 1,
  "device_id": "0194c7b0-2000-7000-8000-000000000001",
  "batch_id": "0194c7b0-6000-7000-8000-000000000001",
  "events": [
    {
      "event_id": "0194c7b0-7000-7000-8000-000000000001",
      "event_type": "lesson.completed",
      "schema_version": 1,
      "school_id": "0194c7b0-0000-7000-8000-000000000001",
      "user_id": "0194c7b0-1000-7000-8000-000000000001",
      "device_id": "0194c7b0-2000-7000-8000-000000000001",
      "entity_type": "lesson",
      "entity_id": "0194c7b0-3100-7000-8000-000000000001",
      "device_sequence": 105,
      "occurred_at": "2026-11-19T12:30:00Z",
      "recorded_at": "2026-11-19T12:30:01Z",
      "payload": {
        "course_id": "0194c7b0-3000-7000-8000-000000000001",
        "completion_percentage": 100
      }
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "batch_id": "0194c7b0-6000-7000-8000-000000000001",
  "protocol_version": 1,
  "acknowledged": [
    "0194c7b0-7000-7000-8000-000000000001"
  ],
  "duplicates": [],
  "rejected": [],
  "requires_review": [],
  "server_cursor": "cursor-0194c7b0-8000"
}
```

### 5.2 Incremental Change Feed
- **Endpoint:** `GET /api/v1/sync/v1/changes`
- **Auth:** Bearer Token
- **Query Params:** `cursor` (optional cursor identifier)

**Response (200 OK):**
```json
{
  "server_cursor": "cursor-0194c7b0-9000",
  "has_more": false,
  "changes": [
    {
      "entity_type": "course",
      "entity_id": "0194c7b0-3000-7000-8000-000000000001",
      "change_type": "updated",
      "version": 3,
      "created_at": "2026-11-19T12:20:00Z"
    }
  ]
}
```

### 5.3 Sync Status
- **Endpoint:** `GET /api/v1/sync/v1/status`
- **Auth:** Bearer Token

**Response (200 OK):**
```json
{
  "protocol_version": 1,
  "server_time": "2026-11-19T12:45:00Z",
  "device_id": "0194c7b0-2000-7000-8000-000000000001",
  "last_sync_at": "2026-11-19T12:30:05Z",
  "last_processed_sequence": 105,
  "server_cursor": "cursor-0194c7b0-8000"
}
```

---

## 6. Assessments & Quizzes

### 6.1 Get Assessment (Student View)
- **Endpoint:** `GET /api/v1/assessments/{assessment_id}`
- **Auth:** Bearer Token
- **Note:** Excludes `correct_answer_json` and explanations for students.

**Response (200 OK):**
```json
{
  "id": "0194c7b0-9100-7000-8000-000000000001",
  "title": "Fractions Quiz 1",
  "time_limit_seconds": 900,
  "total_marks": 10.0,
  "questions": [
    {
      "id": "0194c7b0-9200-7000-8000-000000000001",
      "question_type": "mcq",
      "question_text": "What is 1/2 + 1/4?",
      "options_json": ["1/2", "3/4", "2/6", "1"],
      "marks": 2.0,
      "sequence_number": 1
    }
  ]
}
```

### 6.2 Submit Assessment Attempt
- **Endpoint:** `POST /api/v1/assessments/{assessment_id}/attempts`
- **Auth:** Bearer Token

**Request Body:**
```json
{
  "attempt_id": "0194c7b0-9300-7000-8000-000000000001",
  "device_id": "0194c7b0-2000-7000-8000-000000000001",
  "started_at": "2026-11-19T12:15:00Z",
  "submitted_at": "2026-11-19T12:28:00Z",
  "answers": [
    {
      "question_id": "0194c7b0-9200-7000-8000-000000000001",
      "answer_json": "3/4"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "attempt_id": "0194c7b0-9300-7000-8000-000000000001",
  "status": "graded",
  "score": 10.0,
  "maximum_score": 10.0,
  "grading_status": "automatic"
}
```

---

## 7. System Health & Discovery

### 7.1 Server Health & Heartbeat
- **Endpoint:** `GET /api/v1/health`
- **Auth:** Public

**Response (200 OK):**
```json
{
  "status": "healthy",
  "school_server": {
    "name": "Local School Alpha",
    "version": "1.0.0",
    "database": "sqlite_connected",
    "storage_free_bytes": 192837465600,
    "active_clients_est": 24,
    "mode": "offline-local"
  }
}
```

**End of document.**
