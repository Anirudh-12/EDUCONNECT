# AGENTS.md — School Server (`educonnect-server`)

## Component Overview
`educonnect-server` is the Python + FastAPI modular monolith school server. It provides local authoritative records, authentication, learning content delivery, assessment evaluation, and idempotent event synchronization. It runs on a Raspberry Pi 5 or low-cost school mini-PC with zero active internet connectivity.

## Specifications & Contracts
Before writing or modifying server code, you MUST review:
- Architecture: [educonnect-docs/ARCHITECTURE.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/ARCHITECTURE.md)
- Data Model: [educonnect-docs/DATA_MODEL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DATA_MODEL.md)
- Sync Protocol: [educonnect-docs/SYNC_PROTOCOL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/SYNC_PROTOCOL.md)
- API Specification: [educonnect-docs/API_SPECIFICATION.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/API_SPECIFICATION.md)
- Shared Schemas: [educonnect-protocol/schemas/sync_event.json](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-protocol/schemas/sync_event.json)

## Architectural Invariants for Agents
1. **Modular Monolith Discipline:**
   - Server modules: `identity`, `classroom`, `content`, `learning`, `assessment`, `sync`, `admin`.
   - Do NOT execute cross-module direct database table queries. Interact through internal module service interfaces.
2. **Data Authority:**
   - Server is authoritative for users, classrooms, published courses, official assignment definitions, and official grades.
   - P2P devices and student tablets must NEVER become authorities for permissions or grades.
3. **Idempotent Sync Ingestion:**
   - Every event has a globally unique `event_id`.
   - The sync inbox has a unique constraint on `(school_id, event_id)`.
   - Ingesting the same event ID twice MUST return the previous acknowledgement without re-executing business logic.
4. **Resumable Content Delivery:**
   - Content files are stored on the filesystem, NEVER as large blobs in SQLite.
   - All download endpoints must support HTTP `Range` headers and compute SHA-256 digests.
5. **Zero Internet Requirement:**
   - Never require external API calls, DNS lookups, or cloud auth (OAuth, Firebase) during runtime.

## Tech Stack & Tooling
- Python 3.12+
- FastAPI, Pydantic v2
- SQLAlchemy 2.0 (SQLite default, PostgreSQL compatible)
- Alembic for database migrations
- Pytest for test execution
