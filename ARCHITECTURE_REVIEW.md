# System Architecture Review - Gulf Watch
**Date:** 2026-03-02
**Reviewer:** Ares
**Score:** 7/10

## Executive Summary
Gulf Watch uses a modern, cost-effective architecture: FastAPI backend, React frontend, PostgreSQL/PostGIS database, deployed on Render (free tier). Well-suited for current load but needs changes for scale.

## Architecture Overview

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│  Vercel         │ ◄─────────────►│  Render          │
│  (React SPA)    │                │  (FastAPI)       │
│  gulfwatch.     │                │  gulf-watch-api  │
│    vercel.app   │                │    .onrender.com │
└─────────────────┘                └────────┬─────────┘
                                            │
                                            │ SQL
                                            ▼
                                   ┌──────────────────┐
                                   │  PostgreSQL      │
                                   │  + PostGIS       │
                                   │  (Render)        │
                                   └──────────────────┘
```

## Component Analysis

### 1. Frontend (Vercel)
**Tech:** React 18 + Vite + TypeScript
**Score:** 8/10

**Strengths:**
- Minimal dependencies (only React)
- Fast builds with Vite
- TypeScript for type safety
- Static hosting = infinite scale

**Weaknesses:**
- Simulated map (no real map library)
- Hardcoded API URL
- No SSR/SEO

**Scaling Path:**
- Current: ✅ Good for 10K+ users
- Future: Add Next.js for SSR if SEO needed

### 2. Backend (Render)
**Tech:** FastAPI + SQLAlchemy + Uvicorn
**Score:** 8/10

**Strengths:**
- Async by default (FastAPI + Uvicorn)
- SQLAlchemy 2.0 with type hints
- Geo queries via PostGIS
- Auto-generated OpenAPI docs

**Weaknesses:**
- Free tier = 15min spin-down (cold starts)
- Single instance (no HA)
- No caching layer

**Scaling Path:**
- Current: ✅ Handles ~100 concurrent
- Future: Upgrade to Render Starter ($7/mo) for always-on
- Future: Add Redis for caching
- Future: Read replicas for DB

### 3. Database (PostgreSQL + PostGIS)
**Score:** 9/10

**Strengths:**
- ACID compliance
- PostGIS for geospatial queries
- Free tier sufficient for MVP
- Managed backups

**Weaknesses:**
- No read replicas (free tier)
- Connection limits (free tier)

**Scaling Path:**
- Current: ✅ 10K incidents = ~100MB
- Future: Upgrade to paid PostgreSQL
- Future: Partition by date for performance

### 4. Data Ingestion (Twitter API)
**Score:** 6/10

**Current:** Manual trigger via `/admin/ingest-twitter`
**Issue:** Not automated, relies on manual polling

**Recommended:**
```python
# Add Celery + Redis for scheduled tasks
@celery.task
def ingest_twitter_job():
    # Runs every 5 minutes
    ...
```

## Architecture Decision Record (ADR)

### ADR-001: Monolith over Microservices
**Status:** Accepted

**Context:** MVP stage, small team, rapid iteration needed.

**Decision:** Single FastAPI monolith.

**Consequences:**
- ✅ Simpler deployment
- ✅ Easier debugging
- ✅ Lower complexity
- ❌ Harder to scale independently
- ❌ Single deploy unit

**When to Revisit:** >10K daily active users

### ADR-002: Serverless Frontend over SSR
**Status:** Accepted

**Context:** SEO not critical, speed of deployment matters.

**Decision:** Static React SPA on Vercel.

**Consequences:**
- ✅ Instant deploys
- ✅ Global CDN
- ✅ $0 cost
- ❌ No SEO
- ❌ Initial load requires JS

### ADR-003: Render over AWS/GCP
**Status:** Accepted

**Context:** Zero ops overhead needed, $0 budget.

**Decision:** Render free tier for everything.

**Consequences:**
- ✅ Zero config
- ✅ Automatic deploys
- ✅ Free tier generous
- ❌ Vendor lock-in
- ❌ Less control

## Scalability Analysis

### Current Capacity (Free Tier)
| Metric | Limit | Current |
|--------|-------|---------|
| API Requests/min | ~100 | <10 |
| Database size | 1GB | ~10MB |
| Concurrent users | ~50 | <5 |
| Cold start | 15s | N/A |

### Breaking Points
1. **500 concurrent users** - Need Render Starter plan
2. **10K incidents/day** - Need Redis cache
3. **100K incidents** - Need DB partitioning
4. **Global users** - Need CDN for API

## Security Architecture

```
┌─────────────────────────────────────┐
│  1. HTTPS (Vercel/Render)           │
├─────────────────────────────────────┤
│  2. CORS (configured)               │
├─────────────────────────────────────┤
│  3. SQLAlchemy ORM (injection safe) │
├─────────────────────────────────────┤
│  4. Input Validation (Pydantic)     │
├─────────────────────────────────────┤
│  5. Secrets in Env Vars             │
└─────────────────────────────────────┘

⚠️ Missing:
   - Rate limiting
   - WAF
   - API authentication
```

## Monitoring & Observability

**Current:** None

**Needed:**
- Structured logging (JSON)
- Error tracking (Sentry)
- Metrics (Prometheus/Grafana)
- Uptime monitoring (UptimeRobot)

## Cost Projection

| Users/Month | Current | Recommended |
|-------------|---------|-------------|
| <1K | $0 | $0 |
| 1K-10K | $0 | $7 (Render Starter) |
| 10K-50K | $0* | $25 (Starter + Redis) |
| 50K+ | $0* | $100+ (Multiple services) |

*Free tier would break at these levels

## Recommendations

### Immediate (This Week)
1. ✅ Architecture is sound for MVP

### Short-term (Next Month)
2. Add Redis for caching (Render Redis)
3. Add Celery for background jobs
4. Implement structured logging

### Medium-term (3 Months)
5. Upgrade to Render Starter ($7/mo)
6. Add read replica for DB
7. Implement CDN for static assets

### Long-term (6+ Months)
8. Consider GraphQL for complex queries
9. Add WebSocket for real-time updates
10. Multi-region deployment if global

## Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| AWS Lambda | Infinite scale | Complex, cold starts | ❌ Not chosen |
| Vercel + Neon | Edge deployment | Newer tech | ❌ Not chosen |
| Firebase | Real-time built-in | Vendor lock-in | ❌ Not chosen |
| Render (current) | Simple, $0 | Less control | ✅ Chosen |

## Score: 7/10

**Solid MVP architecture.** Cost-effective, modern stack, clear scaling path. Missing caching, background jobs, and monitoring for production.
