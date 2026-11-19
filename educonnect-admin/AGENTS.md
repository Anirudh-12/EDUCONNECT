# AGENTS.md — Teacher & Admin Portal (`educonnect-admin`)

## Component Overview
`educonnect-admin` is the web application for teachers and school administrators. It provides interfaces for student enrollment, classroom organization, course creation, content uploading, quiz authoring, grading, and server system health monitoring.

## Specifications & Contracts
Before writing code in this repository, review:
- Architecture: [educonnect-docs/ARCHITECTURE.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/ARCHITECTURE.md)
- Data Model: [educonnect-docs/DATA_MODEL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DATA_MODEL.md)
- API Specification: [educonnect-docs/API_SPECIFICATION.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/API_SPECIFICATION.md)
- Visual Identity: [educonnect-docs/DEVELOPMENT_GUIDELINES.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DEVELOPMENT_GUIDELINES.md)

## Core Guidelines for Agents
1. **Local Network Operation (No Internet / No External CDNs):**
   - The web app runs on a local school server. All fonts, icons, styles, and scripts must be bundled locally into the build output.
   - Never import scripts or styles from Google Fonts, unpkg, cdnjs, or other remote CDN services.
2. **Visual Identity:**
   - Adhere strictly to the **Purple, White, and Black** design system.
   - Primary: `#6C47FF`, Deep Container: `#4D2DB7`, Dark Surface: `#18181F`, Text: `#FFFFFF`.
3. **Role-Based Views:**
   - Teacher View: Classroom roster, course and lesson management, content uploads, quiz grading, assignment submissions.
   - Admin View: User provisioning, device registration approval/revocation, server storage metrics, backup/restore.
4. **API Integration:**
   - Call endpoints documented in `/api/v1/` using typed API clients.
   - Attach JWT Bearer token in request headers.

## Tech Stack
- Vue 3 (Composition API `<script setup lang="ts">`)
- TypeScript
- Vite
- Pinia for state management
- Tailwind CSS
- Axios or native `fetch`
