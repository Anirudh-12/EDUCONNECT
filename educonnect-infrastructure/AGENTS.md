# AGENTS.md — Infrastructure & Deployment (`educonnect-infrastructure`)

## Component Overview
`educonnect-infrastructure` contains deployment automation, Docker Compose configurations, server setup scripts, local network DNS/mDNS configurations, and backup/restore scripts for the EDUCONNECT school server.

## Hardware & Environment Targets
- **Hardware:** Raspberry Pi 5 (8 GB RAM) or equivalent low-cost mini-PC (Intel N100).
- **Storage:** 256 GB SSD (configured with `/storage/content` for educational media).
- **Network:** Local offline Wi-Fi access point / router; Ethernet connection where available.
- **Operating System:** Linux (Debian / Raspberry Pi OS / Ubuntu Server).

## Invariants & Rules
1. **Zero Internet Requirement:**
   - The deployment must boot, initialize the database, serve the admin UI, and process student API requests with physical WAN cables disconnected.
   - Container images and dependencies must be pre-built or cacheable without runtime `pip install` or `npm install` over the internet.
2. **Persistence Guarantee:**
   - Both the SQLite database and `/storage/content` must be mounted on persistent host volumes.
3. **Backup & Restore:**
   - Automated scripts must take consistent snapshots of the SQLite database and sync with content storage before creating exportable backup archives.
