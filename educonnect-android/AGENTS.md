# AGENTS.md — Android Student App (`educonnect-android`)

## Component Overview
`educonnect-android` is the student-facing Android client. It is engineered with an **offline-first** design philosophy: students must be able to view previously downloaded lessons, complete offline quizzes, read documents, and log learning activity completely without an active network connection.

## Technical Specifications
Agents working on this repository must read:
- Architecture: [educonnect-docs/ARCHITECTURE.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/ARCHITECTURE.md)
- Synchronization Protocol: [educonnect-docs/SYNC_PROTOCOL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/SYNC_PROTOCOL.md)
- Data Model: [educonnect-docs/DATA_MODEL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DATA_MODEL.md)
- Visual Identity: [educonnect-docs/DEVELOPMENT_GUIDELINES.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DEVELOPMENT_GUIDELINES.md)

## Core Architectural Invariants
1. **Offline Persistence First:**
   - Every student action (e.g. `lesson.started`, `lesson.completed`, `assessment.answer_saved`) must be committed to Room database entities and appended to `sync_outbox` in the same local database transaction.
   - The user must NEVER be blocked from learning because of server reachability.
2. **Persistent Outbox & WorkManager:**
   - The outbox table (`sync_outbox`) tracks events with status: `pending`, `in_flight`, `acknowledged`, `rejected`, `requires_review`.
   - Android `WorkManager` handles opportunistic and periodic synchronization batches when connected to the school server.
   - Failed synchronization attempts must use exponential backoff with jitter and NEVER drop queued events.
3. **Verified Content Storage:**
   - Content downloads support HTTP Range requests for interrupted download resumption.
   - Content files are downloaded to temporary files, and their SHA-256 hash verified before being committed to persistent local storage and marked available.
4. **Visual Identity:**
   - Strict adherence to the **Purple, White, and Black** design language.
   - Primary: `#6C47FF`, Deep Container: `#4D2DB7`, Dark Surface: `#18181F`, Text: `#FFFFFF`.
5. **No Authoritative Grade Generation:**
   - Client records student answers and raw attempts; official scores and grade records are server-authoritative.

## Tech Stack
- Kotlin 2.0+
- Jetpack Compose with Material 3
- Room / SQLite for local persistence
- Android WorkManager for background sync
- Android Network Service Discovery (NSD) for mDNS school server discovery
- Retrofit / OkHttp with Range request interceptors
