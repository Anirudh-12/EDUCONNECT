# EDUCONNECT — Development & Contribution Guidelines

**Document:** DEVELOPMENT_GUIDELINES.md  
**Version:** 1.0  
**Status:** Baseline standards  

---

## 1. Visual Identity & Brand System

EDUCONNECT adheres strictly to a cohesive **Purple, White, and Black** design system across both the Android application and the Web Admin portal. This identity balances a modern, engaging aesthetic with high contrast and readability required for varied classroom lighting conditions.

### 1.1 Color Palette

| Token Name | Hex Code | Purpose & Usage |
| :--- | :--- | :--- |
| **Primary Purple** | `#6C47FF` | Primary action buttons, active states, key interactive indicators |
| **Deep Purple** | `#4D2DB7` | App bar accents, headers, primary container backgrounds |
| **Lavender Accent** | `#A388FF` | Focus rings, secondary highlights, tag badges |
| **Dark Background** | `#0E0E12` | Dark mode background (battery saving on OLED tablets) |
| **Dark Surface** | `#18181F` | Cards, dialogue surfaces, elevated components |
| **Dark Border** | `#2B2B36` | Card dividers, subtle container borders |
| **Pure White** | `#FFFFFF` | Primary text in dark mode, background in high-contrast light mode |
| **Muted Text** | `#9CA3AF` | Secondary labels, timestamps, disabled hints |
| **Success Green** | `#10B981` | Completed lesson indicators, sync success badges |
| **Warning Amber** | `#F59E0B` | Sync pending, network warning |
| **Error Red** | `#EF4444` | Sync rejected, failed validation |

### 1.2 Typography
- Android: Roboto / System Sans with bold hierarchy for headlines and generous touch targets (min 48dp).
- Web Admin: Inter / Plus Jakarta Sans with clear data-density scaling.

---

## 2. Code Standards by Technology

### 2.1 Backend (`educonnect-server` — Python 3.12+)
- **Style & Linting:** Strict compliance with `ruff` and `black`. Line length: 88 chars.
- **Type Annotations:** Full type hint coverage (`mypy` compliant). Avoid `Any`.
- **Validation:** Pydantic v2 schemas for all request/response models.
- **Database:** SQLAlchemy 2.0 style queries (`select()`, `execute()`).
- **Modularity:** Respect module boundaries:
  - Modules: `identity`, `classroom`, `content`, `learning`, `assessment`, `sync`, `admin`.
  - Modules communicate through internal service functions, never cross-querying private tables directly.
- **Errors:** Raise domain-specific exceptions mapped to standard HTTP error envelopes via FastAPI exception handlers.

### 2.2 Android Client (`educonnect-android` — Kotlin)
- **Architecture:** Unidirectional Data Flow (MVI/MVVM).
- **UI:** Jetpack Compose with Material 3 theming customized to the Purple/White/Black palette.
- **Persistence:** Room with typed Converters and schema export enabled. All disk operations on `Dispatchers.IO`.
- **Background Tasks:** Android `WorkManager` with `Constraints.Builder()` ensuring network-bound tasks only trigger when connected.
- **Offline Invariant:** UI must render completely from local Room cache. Remote network fetches must never block or prevent viewing cached lessons.

### 2.3 Web Admin (`educonnect-admin` — Vue 3 + TypeScript)
- **Structure:** Vite + Vue 3 `<script setup lang="ts">`.
- **State:** Pinia for modular state management.
- **Styling:** Tailwind CSS with the brand colors configured in `tailwind.config.ts`.
- **Offline Resilience:** Admin client must work on local LAN without internet access. Assets must not load from external CDNs.

---

## 3. Git Workflow & Version Control

### 3.1 Branching Strategy
- `main`: Production-ready, deployable baseline.
- `develop`: Integration branch for active feature development.
- `feature/<name>`: New feature implementations.
- `fix/<name>`: Bug fixes and issue resolutions.

### 3.2 Commit Messages
Enforce [Conventional Commits](https://www.conventionalcommits.org/):
- `feat(sync): add monotonic conflict resolution for lesson progress`
- `fix(content): verify SHA-256 before writing completed file`
- `docs(api): document resumable range request headers`
- `test(server): add test for duplicate event batch idempotency`
- `refactor(android): migrate outbox worker to CoroutineWorker`

---

## 4. Security & Safety Checklist

- [ ] **No Plaintext Passwords:** Argon2 or bcrypt hashing only.
- [ ] **Device Revocation Check:** Sync requests verify `devices.status == 'active'`.
- [ ] **Local Wi-Fi Zero Trust:** Authenticate every request with JWT; validate device registration signatures.
- [ ] **Content Verification:** Always verify SHA-256 before marking content as accessible.
- [ ] **Student Privacy:** Minimally collect student information; do not mandate email addresses.
- [ ] **Data Durability:** Never delete an unsynchronized outbox event upon network failure.

---

## 5. Working with AI Coding Agents

When delegating tasks to AI agents:
1. Direct the agent to the relevant repository's `AGENTS.md`.
2. Ensure the agent references the cross-repository contracts in `educonnect-protocol` and `educonnect-docs`.
3. Require the agent to run automated unit/integration tests before finalizing changes.
4. Forbid changing protocol schemas or entity models without updating `educonnect-protocol`.

**End of document.**
