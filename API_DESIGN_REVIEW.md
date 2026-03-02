# API Design Review - Gulf Watch
**Date:** 2026-03-02
**Reviewer:** Ares
**Score:** 7/10

## Executive Summary
Gulf Watch API follows REST conventions with good resource naming and proper HTTP methods. Several improvements needed for production readiness: versioning, pagination, and consistent error formats.

## Strengths ✅

### Resource-Based URLs
```
GET    /incidents              ✅ Good - plural nouns
GET    /incidents/{id}         ✅ Good - resource by ID
GET    /incidents/nearby       ✅ Good - sub-resource
POST   /reports                ✅ Good - submission endpoint
GET    /sources/official       ✅ Good - filtered collection
```

### HTTP Methods
| Endpoint | Method | Correct? |
|----------|--------|----------|
| `/incidents` | GET | ✅ Read collection |
| `/reports` | POST | ✅ Create resource |
| `/subscriptions` | POST | ✅ Create resource |
| `/subscriptions/{token}` | DELETE | ✅ Remove resource |
| `/admin/init-db` | GET/POST | ⚠️ Should be POST only |

### Status Codes
- 200 for successful reads ✅
- 201 for successful creation ✅
- 400 for invalid input ✅
- 404 for not found ✅
- 500 for server errors ✅

### Query Parameters
```python
# Good: Proper validation
lat: float = Query(..., ge=-90, le=90)
lng: float = Query(..., ge=-180, le=180)
radius: float = Query(50.0, ge=1, le=500)
```

## Issues ⚠️

### 1. No API Versioning
**Current:** `/incidents`
**Recommended:** `/api/v1/incidents`

**Why:** Breaking changes can't be rolled out safely.

### 2. Inconsistent Error Format
**Current:** Mixed formats
```python
# Format 1
raise HTTPException(status_code=500, detail="message")

# Format 2
return {"status": "error", ...}
```

**Recommended:** Standardized error schema
```json
{
  "error": {
    "code": "INCIDENT_NOT_FOUND",
    "message": "Incident not found",
    "status": 404,
    "timestamp": "2026-03-02T12:00:00Z"
  }
}
```

### 3. No Pagination on Collections
**Current:** `GET /incidents` returns all
**Risk:** Unbounded response size

**Recommended:**
```
GET /incidents?limit=20&offset=0
GET /incidents?limit=20&cursor=eyJpZCI6MTIzfQ
```

### 4. Admin Endpoints Not Namespaced
**Current:** `/admin/init-db`
**Recommended:** `/api/v1/admin/database/init`

### 5. Missing Filtering/Sorting
**Current:** No query filters beyond `min_status`
**Recommended:**
```
GET /incidents?country=UAE&status=CONFIRMED
GET /incidents?sort=-detected_at&event_type=drone
GET /incidents?since=2026-03-01T00:00:00Z
```

### 6. Inconsistent Date Formats
**Current:** Mixed ISO 8601 and local strings
**Recommended:** All dates in UTC ISO 8601

### 7. No HATEOAS or Self-Links
**Recommended:** Include navigation links
```json
{
  "id": "123",
  "links": {
    "self": "/api/v1/incidents/123",
    "reports": "/api/v1/incidents/123/reports"
  }
}
```

## Recommended API Spec (OpenAPI)

```yaml
openapi: 3.0.0
info:
  title: Gulf Watch API
  version: 1.0.0

paths:
  /api/v1/incidents:
    get:
      summary: List incidents
      parameters:
        - name: limit
          in: query
          schema: { type: integer, default: 50, maximum: 200 }
        - name: cursor
          in: query
          schema: { type: string }
        - name: country
          in: query
          schema: { type: string, enum: [UAE, Saudi, Qatar, Bahrain] }
        - name: status
          in: query
          schema: { type: string, enum: [CONFIRMED, LIKELY, PROBABLE] }
        - name: sort
          in: query
          schema: { type: string, default: '-detected_at' }
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  data: { type: array, items: { $ref: '#/components/schemas/Incident' } }
                  pagination:
                    type: object
                    properties:
                      next_cursor: { type: string }
                      has_more: { type: boolean }

  /api/v1/incidents/{id}:
    get:
      summary: Get incident details
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        200:
          content:
            application/json:
              schema: { $ref: '#/components/schemas/IncidentDetail' }
        404:
          $ref: '#/components/responses/NotFound'
```

## GraphQL Alternative (Future)

For complex queries, consider GraphQL:
```graphql
query GetIncidentsNearLocation {
  incidents(
    near: { lat: 25.2, lng: 55.3, radius: 50 }
    filter: { status: CONFIRMED, country: UAE }
    sort: { field: detected_at, order: DESC }
    limit: 20
  ) {
    id
    status
    location { name lat lng }
    description
    detectedAt
  }
}
```

## Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| 🔴 High | Add `/api/v1` prefix | 1 hour |
| 🔴 High | Implement cursor pagination | 2 hours |
| 🟡 Medium | Standardize error format | 2 hours |
| 🟡 Medium | Add filtering/sorting params | 3 hours |
| 🟢 Low | Create OpenAPI spec | 4 hours |
| 🟢 Low | Add HATEOAS links | 3 hours |

## Score: 7/10

**Good foundation** - REST conventions followed, proper HTTP semantics. **Needs work** on versioning, pagination, and consistency for production use.
