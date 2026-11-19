# AGENTS.md — Synchronization & Networking (`educonnect-sync`)

## Component Overview
`educonnect-sync` owns synchronization transport, school server network discovery, resumable file transfers, network connectivity monitoring, and incremental peer-to-peer (P2P) content distribution.

## Technical Specifications
Before implementing or modifying synchronization logic:
- Protocol Specification: [educonnect-docs/SYNC_PROTOCOL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/SYNC_PROTOCOL.md)
- Architecture: [educonnect-docs/ARCHITECTURE.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/ARCHITECTURE.md)
- Data Model: [educonnect-docs/DATA_MODEL.md](file:///c:/Users/aksha/OneDrive/Documents/educonnect/educonnect-docs/DATA_MODEL.md)

## Agent Responsibilities & Invariants
1. **Transport Separation from Semantics:**
   - `educonnect-sync` coordinates the safe, verified delivery of event payloads and binary files. It does NOT define the semantic meaning of learning progress or grades.
2. **Idempotency & Resumption:**
   - Every file download session must support HTTP Range requests and resume from the last byte received.
   - Event delivery must enforce exponential backoff with jitter on network failure.
3. **P2P Boundary:**
   - Peer-assisted distribution is strictly limited to immutable, published content binaries (PDFs, videos, packages).
   - Peer devices must NEVER synchronize or validate authoritative learning records, user permissions, or official grades.
4. **Content Integrity:**
   - No content file may be marked as valid without strict SHA-256 hash calculation and verification against the school server manifest.
