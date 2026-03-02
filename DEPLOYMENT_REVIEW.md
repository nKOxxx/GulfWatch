# Render Deployment Review - Gulf Watch
**Date:** 2026-03-02
**Reviewer:** Ares
**Score:** 8/10

## Deployment Status

| Service | Status | URL | Plan |
|---------|--------|-----|------|
| Backend API | ✅ Live | https://gulf-watch-api.onrender.com | Free |
| Frontend | ✅ Live | https://gulfwatch.vercel.app | Free |
| Database | ✅ Live | gulf-watch-db | Free |

## Blueprint Analysis

### Current `render.yaml`
```yaml
services:
  - type: web
    name: gulf-watch-api
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: cd backend && python -m uvicorn src.api_v2:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: gulf-watch-db
          property: connectionString

databases:
  - name: gulf-watch-db
    databaseName: gulfwatch
    user: gulfwatch
    plan: free
```

### Strengths ✅
- Blueprint-based deployment (IaC)
- Auto-deploy on git push
- Database connection via env var
- Python version pinned

### Issues ⚠️

#### 1. Missing Environment Variables
**Current:** Only `DATABASE_URL` and `PYTHON_VERSION`
**Missing:**
- `TWITTER_BEARER_TOKEN` (for ingestion)
- `SECRET_KEY` (for future auth)
- `ENVIRONMENT` (dev/staging/prod)
- `LOG_LEVEL`

#### 2. No Health Check
**Add to render.yaml:**
```yaml
healthCheckPath: /api/health
```

**Add to api_v2.py:**
```python
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

#### 3. No Auto-Deploy Restrictions
**Risk:** Every push deploys to production

**Fix:** Add branch filter
```yaml
# render.yaml (not currently supported, use dashboard)
# Or use GitHub Actions for staging
```

#### 4. Cold Start Issue
**Current:** Free tier spins down after 15min
**Impact:** 15-30s cold start on first request

**Solutions:**
- Upgrade to Starter ($7/mo) for always-on
- Ping service (UptimeRobot) every 10min
- Acceptable for MVP stage

## Deployment Checklist

### Pre-Deploy ✅
- [x] render.yaml in repo root
- [x] requirements.txt exists
- [x] GitHub repo connected
- [x] Database created

### Post-Deploy ⚠️
- [ ] Add missing env vars (Twitter token)
- [ ] Test `/api/health` endpoint
- [ ] Verify CORS allows Vercel domain
- [ ] Check database migrations run
- [ ] Add log drain (Papertrail/Sentry)

## Environment Variables Setup

**From AgentVault or dashboard:**
```
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAA...
SECRET_KEY=your-random-secret-key
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Vercel Configuration

### Current Setup
- Git repo: `nKOxxx/GulfWatch`
- Build command: `npm run build`
- Output directory: `dist`

### Missing `vercel.json`
Should add:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ]
}
```

## Monitoring Setup

### Current: None

### Recommended (Free):
1. **UptimeRobot** - Ping API every 5min (prevents cold start + alerts)
2. **Sentry** - Error tracking (free tier)
3. **Render Logs** - Built-in log streaming

## Cost Analysis

| Component | Current | Recommended |
|-----------|---------|-------------|
| Web Service | Free ($0) | Starter ($7/mo) |
| Database | Free ($0) | Starter ($7/mo) |
| Vercel | Free ($0) | Free ($0) |
| **Total** | **$0** | **$14/mo** |

## Scaling Path

### Phase 1: MVP (Current)
- Free tier everything
- Accept cold starts
- Manual Twitter ingestion

### Phase 2: Always-On ($14/mo)
- Render Starter web service
- Render Starter database
- UptimeRobot pings

### Phase 3: Production ($50-100/mo)
- Multiple web service instances
- Redis cache
- Read database replica
- CDN (Cloudflare)

## Troubleshooting Guide

### Build Failures
```bash
# Check logs in Render dashboard
# Common issues:
# 1. Missing requirements.txt
# 2. Import errors (check PYTHONPATH)
# 3. Database connection timeout
```

### Database Connection Issues
```bash
# Test connection locally:
psql $DATABASE_URL -c "SELECT 1"

# Check if PostGIS enabled:
# SELECT PostGIS_Version();
```

### CORS Errors
```python
# Update api_v2.py:
allow_origins=[
    "https://gulfwatch.vercel.app",
    "http://localhost:5173"  # dev
]
```

## Security Recommendations

1. **Add deploy hooks** - Require manual approval for production
2. **Enable preview deploys** - Test PRs before merging
3. **Secrets rotation** - Rotate Twitter token quarterly
4. **DB backups** - Enable automatic backups (paid feature)

## Score: 8/10

**Excellent deployment setup.** Blueprint-based, auto-deploy, proper env var handling. Missing: health checks, staging environment, and monitoring.
