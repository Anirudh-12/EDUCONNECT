# EDUCONNECT — Product & Engineering Roadmap

**Document:** ROADMAP.md  
**Version:** 1.0  
**Status:** Living roadmap baseline  

---

## 1. Vision & Trajectory

EDUCONNECT bridges the digital divide for educational communities lacking stable internet connectivity. The engineering roadmap is structured into phased horizons, moving from an offline-first modular client-server baseline to peer-to-peer distribution and offline local AI assistance.

---

## 2. Horizons

### Horizon 1: Offline-First MVP (Current Focus)
**Target:** Single school server, up to 50 active Android devices, local Wi-Fi.

- **Server:** Python + FastAPI + SQLAlchemy + SQLite running on Raspberry Pi 5 / low-cost mini-PC.
- **Client:** Kotlin + Jetpack Compose Android app with Room local persistence and WorkManager outbox sync.
- **Admin:** Vue 3 + TypeScript dashboard for teachers/administrators.
- **Content:** Local filesystem storage, SHA-256 integrity verification, HTTP chunked/resumable downloads.
- **Sync:** HTTP batch event sync with idempotency tracking and monotonic progress projection.
- **Infrastructure:** Docker Compose one-command bootstrap, zero internet runtime dependency.

---

### Horizon 2: Peer-to-Peer Content Mesh (`educonnect-sync`)
**Target:** Relieve local Wi-Fi bottleneck by distributing heavy content directly between student tablets.

- **P2P Discovery:** Wi-Fi Direct and local mDNS peer discovery.
- **Peer Verification:** Server-signed content tokens authorizing peer transfer; cryptographic SHA-256 validation before marking content active.
- **Bandwidth Optimization:** Devices that already downloaded large video/PDF modules become local seeds for classroom peers.
- **Security Boundary:** Peer-to-peer transport is strictly limited to immutable content binaries. Learning records, assignment submissions, and grades remain strictly client-to-school-server.

---

### Horizon 3: Multi-Classroom Scaling & High Concurrency
**Target:** Medium-to-large institutions (200–500 active devices).

- **Database:** Seamless upgrade path from SQLite to PostgreSQL.
- **Caching & Queue:** Redis for session caches and background processing queues when hardware allows.
- **Enhanced Role-Based Access:** Department heads, multi-grade administrators, parent/guardian viewing portals.
- **Network Resilience:** Mesh access-point coordination and adaptive bit-rate streaming for educational videos.

---

### Horizon 4: Local AI & Offline Intelligence
**Target:** Intelligent learning companion without external cloud API calls.

- **Local Embeddings:** Local vector indexing of textbooks and lesson transcripts.
- **Offline RAG & Search:** Semantic search over the school library stored on the server.
- **Teacher Assistant:** Automatic draft grading for short-answer questions and automated quiz question generation from lesson text.
- **Student Tutoring:** Small quantized open-source models (e.g. Gemma 2B / Qwen) running on school server hardware or modern student devices.

---

### Horizon 5: Inter-School Federation & Sneaker-Net Sync
**Target:** Regional educational districts and periodic hub updates.

- **Periodic Sync:** Opportunistic synchronization when a teacher's laptop or USB drive visits a central regional office with internet.
- **Curriculum Packs:** Exportable/importable signed digital curriculum packages (`.ecpack`) containing course structures, assessments, and content binaries.
- **District Analytics:** Aggregated anonymized learning progress reports returned to educational authorities.

---

## 3. Release Milestones

| Version | Milestone | Expected Core Deliverables |
| :--- | :--- | :--- |
| **v0.1** | Architecture & Protocol Baseline | Directory setup, schemas, data contracts, and agent guidelines. |
| **v0.5** | Core Server & Sync Engine | Auth, device registration, idempotent event ingestion, content download. |
| **v0.8** | Android App & Admin Portal | Room outbox, lesson player, quiz runner, teacher admin portal. |
| **v1.0** | MVP Release | 50-device tested baseline on Raspberry Pi 5 with zero internet dependency. |
| **v1.5** | P2P Distribution Beta | Peer content sharing between Android devices. |
| **v2.0** | Scaled & AI-Enabled | PostgreSQL option, local semantic search, curriculum pack import/export. |

**End of document.**
