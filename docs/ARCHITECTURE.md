# Architecture — Current State

> Updated by: Architect Agent
> Last reviewed: 2026-06-18

## Current Architecture

(To be populated as the system is built.)

## High-Level Diagram

```
[Web (Next.js)] [Mobile (Flutter)]
        |              |
        +------+-------+
               |
       [Cloudflare/CDN]
               |
        [API Gateway]
               |
   +-----------+-----------+
   |     12 Services       |
   | auth, academic, ...   |
   +-----------+-----------+
               |
        [PostgreSQL 16]
        [Pub/Sub (cloud)]
        [Cloud Storage]
```

## Active ADRs

See `docs/DECISIONS.md` for the full list.

## Service Inventory

| Service | Port (local) | Status |
|---------|--------------|--------|
| snx-auth | 8001 | ⚪ Not started |
| snx-academic | 8002 | ⚪ Not started |
| snx-attendance | 8003 | ⚪ Not started |
| snx-exam | 8004 | ⚪ Not started |
| snx-clinical | 8005 | ⚪ Not started |
| snx-logbook | 8006 | ⚪ Not started |
| snx-institution | 8007 | ⚪ Not started |
| snx-compliance | 8008 | ⚪ Not started |
| snx-notification | 8009 | ⚪ Not started |
| snx-workflow | 8010 | ⚪ Not started |
| snx-analytics | 8011 | ⚪ Not started |
| snx-ai | 8012 | ⚪ Not started |

## Data Flow Diagrams

(To be added as modules are built.)

## Event Catalogue

(To be added as Pub/Sub events are defined.)

---
*This document is auto-updated by the Architect Agent after every architecturally significant change.*
