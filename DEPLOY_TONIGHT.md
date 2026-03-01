# Gulf Watch - Tonight's Deployment Checklist

## Goal: Live URL by end of night

---

## Step 1: Render (Backend + Database) ⏱️ 10 minutes

### 1.1 Create PostgreSQL Database
```
1. Go to https://dashboard.render.com
2. Click "New" → "PostgreSQL"
3. Name: gulf-watch-db
4. Plan: Free ($0/month)
5. Click "Create Database"
6. Copy the "Internal Database URL" 
```

### 1.2 Deploy Backend
```
1. In Render dashboard, click "New" → "Web Service"
2. Connect GitHub: nKOxxx/GulfWatch
3. Name: gulf-watch-api
4. Root Directory: backend
5. Build Command: pip install -r requirements.txt
6. Start Command: python -m uvicorn src.api_v2:app --host 0.0.0.0 --port $PORT
7. Click "Advanced"
8. Add Environment Variable:
   - Key: DATABASE_URL
   - Value: [paste from step 1.1]
9. Click "Create Web Service"
```

### 1.3 Verify Backend
Wait for deploy (2-3 min), then visit:
- https://gulf-watch-api.onrender.com/
- Should show: `{"status":"operational",...}`

---

## Step 2: Vercel (Frontend) ⏱️ 5 minutes

```
1. Go to https://vercel.com
2. Click "Add New Project"
3. Import GitHub: nKOxxx/GulfWatch
4. Framework Preset: Vite
5. Root Directory: frontend
6. Build Command: npm run build
7. Output Directory: dist
8. Click "Environment Variables"
9. Add:
   - VITE_API_URL = https://gulf-watch-api.onrender.com
10. Click "Deploy"
```

Wait for deploy (1-2 min), then visit:
- https://gulf-watch.vercel.app (or Vercel-assigned URL)

---

## Step 3: Initialize Database ⏱️ 2 minutes

Once backend is live, run this to create tables:

```bash
# Connect to Render database and run schema
curl -X POST https://gulf-watch-api.onrender.com/admin/init-db
```

Or manually:
```bash
# Get Render database connection string
# Run locally:
psql [RENDER_DATABASE_URL] -f backend/schema.sql
```

---

## Step 4: Test End-to-End ⏱️ 5 minutes

### Test these URLs:
1. ✅ https://gulf-watch-api.onrender.com/ (API status)
2. ✅ https://gulf-watch-api.onrender.com/incidents (empty or demo data)
3. ✅ https://gulf-watch-api.onrender.com/sources/official (UAE sources)
4. ✅ https://gulf-watch.vercel.app (frontend loads)

### Frontend should show:
- Location detection working
- "All Clear" or demo incidents
- Official sources tab populated
- Map and tracking functional

---

## If Something Breaks:

### Backend won't start:
- Check Render logs (dashboard → service → logs)
- Verify DATABASE_URL is set
- Check Python version (should be 3.11)

### Frontend won't build:
- Check Vercel build logs
- Verify VITE_API_URL points to Render backend
- Check Node.js version (should be 18+)

### Database connection fails:
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/db`
- Check if PostgreSQL allows external connections (Render does)
- Try connecting with `psql $DATABASE_URL`

---

## Success Criteria:

- [ ] Backend API responds at / with status 200
- [ ] Database has incidents table (can query /incidents)
- [ ] Frontend loads without errors
- [ ] Location detection works
- [ ] Official sources visible in UI

---

## After Tonight (Phase 2):

Once live, we add:
1. Twitter API integration (real data)
2. WebSocket live updates
3. Push notifications

But MVP is LIVE and SHAREABLE tonight!

---

## URLs to Share:

Once deployed:
- **Frontend**: https://gulf-watch.vercel.app
- **Backend**: https://gulf-watch-api.onrender.com
- **GitHub**: https://github.com/nKOxxx/GulfWatch

Ready to show the network!
