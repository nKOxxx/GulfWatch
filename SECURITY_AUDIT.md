# Security Audit Report - Gulf Watch
**Date:** 2026-03-02
**Auditor:** Ares
**Score:** 6/10

## Executive Summary
Gulf Watch is a threat intelligence platform with a FastAPI backend and React frontend. The security posture is **Good with Fixes Needed** - core architecture is sound but several medium-risk issues need addressing before production scaling.

## Findings

### 🟢 GOOD
| Area | Finding | Status |
|------|---------|--------|
| Secrets Management | Twitter Bearer Token in Render env vars (not code) | ✅ Secure |
| Database | PostgreSQL with SQLAlchemy ORM (parameterized queries) | ✅ SQL Injection Protected |
| CORS | Properly configured in FastAPI | ✅ Present |
| Input Validation | Pydantic models validate all API inputs | ✅ Strong Typing |
| HTTPS | Render enforces TLS termination | ✅ Encrypted |
| Error Handling | Generic error messages don't leak stack traces | ✅ Safe |

### 🟡 MEDIUM RISK
| Issue | Location | Risk | Fix |
|-------|----------|------|-----|
| CORS allows all origins | `api_v2.py:52` | CSRF potential | Restrict to `gulfwatch.vercel.app` |
| No rate limiting | All endpoints | DoS vulnerability | Add `slowapi` or nginx rate limiting |
| No authentication on admin endpoints | `/admin/*` | Unauthorized access | Add API key or JWT auth |
| Missing security headers | All responses | XSS/clickjacking | Add `fastapi.security` headers |
| npm audit vulnerabilities | Frontend | Dev server exposure | Upgrade esbuild via vite@7.3.1 |
| No request logging | Backend | Can't detect attacks | Add middleware logging |
| Database connection not encrypted | `render.yaml` | MITM risk | Add SSL mode to connection string |

### 🔴 HIGH RISK
| Issue | Location | Risk | Fix |
|-------|----------|------|-----|
| Admin endpoints have no auth | Multiple | Full data compromise | Add API key middleware |
| SQL in endpoint queries | `api_v2.py:333` | Potential injection | Use ORM methods only |
| No input sanitization on reports | `/reports` POST | XSS via stored content | Sanitize HTML/JS in content |
| Hardcoded API URL in frontend | `App.tsx:4` | No env flexibility | Use `import.meta.env` |

## Dependency Audit

### Backend (Python)
```
fastapi>=0.104.0       ✅ Current, no CVEs
uvicorn>=0.24.0        ✅ Current
sqlalchemy>=2.0.0      ✅ Current
psycopg2-binary>=2.9.9 ✅ Current
```

### Frontend (npm audit)
```
esbuild <=0.24.2       ⚠️  GHSA-67mh-4wv8-2f99 (Moderate)
vite 5.0.8             ⚠️  Depends on vulnerable esbuild
```
**Fix:** `npm audit fix --force` (will upgrade to vite@7.3.1)

## Scoring Breakdown

| Category | Score | Notes |
|----------|-------|-------|
| Authentication | 3/10 | No auth on endpoints |
| Authorization | 5/10 | Admin routes unprotected |
| Input Validation | 8/10 | Pydantic covers most |
| Output Encoding | 7/10 | React auto-escapes |
| Secrets Management | 9/10 | Proper env var usage |
| Dependency Mgmt | 6/10 | 2 moderate CVEs |
| Logging/Monitoring | 3/10 | No audit logs |
| Data Protection | 7/10 | HTTPS + PostGIS |
| **Overall** | **6/10** | **Good with fixes needed** |

## Recommendations

### Immediate (Critical)
1. **Add admin authentication** - API key or JWT middleware
2. **Fix npm vulnerabilities** - `npm audit fix --force`
3. **Restrict CORS** - Limit to production domains

### Short-term (1-2 weeks)
4. **Add rate limiting** - 100 req/min per IP
5. **Add security headers** - Helmet.js equivalent
6. **Request logging** - All admin actions logged

### Medium-term (1 month)
7. **Database SSL** - Encrypt DB connections
8. **Input sanitization** - XSS protection on report content
9. **API versioning** - `/api/v1/` prefix

## Compliance Notes

- **GDPR:** No PII collection detected ✅
- **SOC2:** Need audit logging for compliance
- **ISO 27001:** Authentication required for admin functions

## Action Priority

1. 🔴 **CRITICAL** - Add auth to admin endpoints
2. 🔴 **CRITICAL** - Fix npm vulnerabilities
3. 🟡 **HIGH** - Implement rate limiting
4. 🟡 **HIGH** - Restrict CORS origins
5. 🟡 **MEDIUM** - Add security headers
6. 🟢 **LOW** - Database SSL mode
