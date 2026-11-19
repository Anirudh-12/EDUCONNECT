# EDUCONNECT — Offline-First Educational Ecosystem

EDUCONNECT is an offline-first digital learning ecosystem engineered for schools with intermittent or completely absent internet connectivity. It provides a local school server, an Android student learning application, a web-based teacher and administration portal, idempotent offline synchronization, and peer-assisted content distribution.

---

## Architecture & Visual Identity

- **Architecture:** Offline-first modular monolith server + native Android client + local web admin.
- **Visual Identity:** Modern Purple, White, and Black palette (`#6C47FF` Primary Purple, `#18181F` Dark Surface, `#FFFFFF` Text).
- **Target Deployment:** Raspberry Pi 5 (8 GB RAM) or low-cost school mini-PC with 256 GB SSD.
- **Initial Target Capacity:** 50 registered students / 20–30 concurrent active devices.

---

## Workspace Directory Structure

```
EDUCONNECT/
├── educonnect-docs/              # Master specifications & architectural source of truth
│   ├── ARCHITECTURE.md           # System architecture, principles, boundaries
│   ├── SYNC_PROTOCOL.md          # ESP event envelope, idempotency, conflict policies
│   ├── DATA_MODEL.md             # Canonical database schema & Room entity specifications
│   ├── API_SPECIFICATION.md      # REST endpoints, schemas, auth, error handling
│   ├── MVP_IMPLEMENTATION_PLAN.md# Task breakdown, dependencies, acceptance checklist
│   ├── ROADMAP.md                # Horizons from MVP to P2P mesh and local AI
│   └── DEVELOPMENT_GUIDELINES.md # Style guides, brand palette, testing & AI guidelines
│
├── educonnect-protocol/          # Authoritative cross-repository contracts
│   ├── AGENTS.md
│   ├── SYNC_PROTOCOL.md
│   ├── DATA_MODEL.md
│   ├── openapi.yaml              # OpenAPI 3.1 specification
│   └── schemas/                  # JSON Schemas (sync_event.json, content_manifest.json)
│
├── educonnect-server/            # Python + FastAPI school server
│   ├── AGENTS.md
│   ├── pyproject.toml / requirements.txt
│   ├── app/                      # Modular monolith (identity, classroom, content, learning, assessment, sync, admin)
│   └── tests/
│
├── educonnect-android/           # Kotlin + Jetpack Compose student app
│   ├── AGENTS.md
│   ├── build.gradle.kts
│   └── app/                      # Offline-first Room DB, WorkManager outbox, M3 UI
│
├── educonnect-admin/             # Vue 3 + TypeScript + Vite web admin portal
│   ├── AGENTS.md
│   ├── package.json
│   └── src/
│
├── educonnect-sync/              # Synchronization transport & P2P distribution
│   └── AGENTS.md
│
└── educonnect-infrastructure/    # Deployment & Docker Compose
    ├── AGENTS.md
    ├── docker-compose.yml
    └── docker/                   # Container definitions for zero-internet deployment
```

---

## Source of Truth for AI Coding Agents

Every subproject includes an `AGENTS.md` file that guides autonomous AI coding agents. Agents working on any component must treat the master specifications in `educonnect-docs/` and contracts in `educonnect-protocol/` as immutable unless authorized to version them.

---

## Quick Start (School Server)

### Prerequisites
- Python 3.12+ (or Docker)
- Local Wi-Fi network

### Running the School Server locally:
```bash
cd educonnect-server
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000/docs](http://localhost:8000/docs) to view interactive Swagger API documentation.

### Running via Docker Compose:
```bash
cd educonnect-infrastructure
docker compose up -d
```
