# API Design Conventions — Synaptix

## URL Structure

```
https://api.synaptix.{domain}/api/{version}/{resource}/{id?}/{sub-resource?}
```

- Always versioned: `/api/v1/`
- Resources are plural: `/students`, `/attendance`, `/exams`
- IDs are UUIDs
- Kebab-case for multi-word resources: `/lesson-plans`, `/clinical-postings`
- Sub-resources for nested: `/students/{id}/attendance`

## HTTP Methods

| Method | Use For |
|--------|---------|
| GET | Read |
| POST | Create OR action endpoints (`/students/{id}/mark-attendance`) |
| PUT | Full replacement (rarely used) |
| PATCH | Partial update |
| DELETE | Soft delete (sets `deleted_at`) |

## Response Envelope

EVERY response uses this envelope:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "timezone": "Asia/Kolkata",
    "request_id": "uuid",
    "api_version": "v1",
    "timestamp": "2026-06-18T14:30:00+05:30"
  },
  "errors": null
}
```

## Pagination

Cursor-based pagination for large lists:

```json
{
  "data": [...],
  "meta": {
    "next_cursor": "eyJpZCI6...",
    "prev_cursor": null,
    "has_more": true,
    "page_size": 50
  }
}
```

Query: `?cursor=eyJpZCI6...&limit=50`

## Filtering

```
GET /api/v1/attendance?student_id=uuid&subject_code=AN&from=2026-01-01&to=2026-06-30
```

- Use query parameters for filters
- Date ranges: `from` and `to` (inclusive)
- Multiple values: comma-separated (`subject_code=AN,PH,BC`)

## Error Codes

Every error has a stable code like `SNX-{SERVICE}-{NUMBER}`:

| Code Range | Service |
|-----------|---------|
| SNX-AUTH-* | Authentication |
| SNX-ATT-* | Attendance |
| SNX-EXM-* | Exam |
| SNX-LOG-* | Logbook |
| SNX-CLI-* | Clinical |
| SNX-NMC-* | NMC compliance violation |
| SNX-VAL-* | Validation |
| SNX-RBAC-* | Permission |
| SNX-TNT-* | Tenant isolation |

## HTTP Status Codes

- 200: Success
- 201: Created
- 204: Success, no content
- 400: Validation error (Pydantic)
- 401: Not authenticated
- 403: Authenticated but lacks permission
- 404: Resource not found
- 409: Conflict (e.g., duplicate)
- 422: Business rule violation (NMC, etc.)
- 429: Rate limit exceeded
- 500: Server error
- 503: Dependency unavailable

## Authentication

All endpoints except `/health`, `/ready`, `/auth/*` require JWT bearer token:

```
Authorization: Bearer {jwt-token}
```

JWT claims:
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "roles": ["faculty", "hod"],
  "session_id": "uuid",
  "iat": 1234567890,
  "exp": 1234567890
}
```

## Rate Limiting

Headers in every response:
```
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 542
X-RateLimit-Reset: 1234567890
```

## Versioning Policy

- Breaking change → new version (v1 → v2)
- Additive change → same version
- Old versions supported 12 months after new version launch
- Deprecation announced via `Deprecation` header and changelog

## OpenAPI Spec

Every service exposes its OpenAPI spec at `/openapi.json` and Swagger UI at `/docs`.

The Architect Agent maintains the canonical spec in `docs/api/`.
