# AGENTS.md — Protocol & Contracts Repository

## Repository Overview
`educonnect-protocol` is the authoritative, single source of truth for all cross-repository contracts in the EDUCONNECT ecosystem. It defines API schemas, synchronization event structures, data exchange formats, and versioning rules.

## Primary References
Before making any changes in this repository, review:
- [educonnect-docs/SYNC_PROTOCOL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/SYNC_PROTOCOL.md)
- [educonnect-docs/DATA_MODEL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DATA_MODEL.md)
- [educonnect-docs/API_SPECIFICATION.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/API_SPECIFICATION.md)

## Agent Responsibilities & Rules
1. **Never Make Breaking Changes Without Version Bumps:**
   - Synchronization events use integer schema versions (`schema_version: 1`). Any structural change requires incrementing this version or creating a new `event_type`.
   - REST endpoints are prefixed with `/api/v1/`. Breaking changes must be versioned.
2. **Schema Authority:**
   - Both `educonnect-server` (Pydantic models) and `educonnect-android` (Room / Kotlin data classes) must conform to schemas defined here.
   - Do not invent fields in server or Android implementations that are not documented in this repository.
3. **Validation Requirements:**
   - All JSON schemas in `schemas/` must be valid Draft 2020-12 / Draft 7 schemas.
   - OpenAPI specs in `openapi.yaml` must pass standard OpenAPI linters.

## Directory Structure
- `schemas/`: JSON schemas for sync events, payloads, and manifests.
- `openapi.yaml`: Authoritative OpenAPI 3.1 specification.
- `SYNC_PROTOCOL.md`: Mirror of the protocol specification.
- `DATA_MODEL.md`: Mirror of the canonical data model.
