# Gulf Watch — Architecture Summary

## What We Built

A **location-based threat intelligence platform** for the Arabian Gulf region. Modular architecture designed for future government and private camera partnerships.

## Project Structure

```
gulf-watch/
├── backend/              # Node.js + Express + PostgreSQL
│   ├── src/
│   │   ├── index.ts         # Main server + WebSocket
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Database, etc.
│   │   └── ingestion/       # Data ingestion (Twitter, etc.)
│   ├── schema.sql           # PostgreSQL + PostGIS schema
│   └── package.json
├── frontend/             # React + Mapbox
│   ├── src/
│   │   ├── App.tsx
│   │   └── components/
│   └── package.json
├── docs/
│   └── SETUP.md
├── Dockerfile
└── README.md
```

## Key Features

### 1. Region-Based Intelligence
- Users select location (Dubai, Abu Dhabi, Bahrain, Doha, Riyadh)
- All data filtered to that region
- Easy to add new regions

### 2. Verification Engine (Database Ready)
- Raw events ingested from multiple sources
- Cross-reference scoring
- AI analysis ready for image/video verification
- Human review capability

### 3. Partnership Framework
- `camera_partnerships` table tracks government/private partnerships
- API endpoint to register new partners
- Status tracking: pending → negotiating → active

### 4. Real-Time Alerts
- WebSocket for live updates
- Severity levels: low, medium, high, critical
- Multi-channel distribution (push, SMS, Telegram ready)

## Data Sources (Current)

| Source | Status | Notes |
|--------|--------|-------|
| Twitter/X | Ready | Needs Bearer Token |
| Telegram | Placeholder | Bot setup required |
| News Feeds | Placeholder | RSS/API integration |
| ADS-B | Placeholder | Aviation tracking |
| Public Cameras | Ready | RTA integration possible |

## Data Sources (Future — Partnerships)

| Source | Type | Integration |
|--------|------|-------------|
| Government security cameras | Government | API or VPN |
| Military early warning | Government | Secure channel |
| Private infrastructure | Private | API or stream |
| Hotel/corporate cameras | Private | Partnership deal |

## Technical Stack

- **Backend:** Node.js, Express, TypeScript, PostgreSQL + PostGIS, Redis
- **Frontend:** React, TypeScript, Mapbox GL
- **Real-time:** WebSocket
- **Queue:** BullMQ (background jobs)
- **Deployment:** Docker, Render/AWS

## Next Steps

### Immediate (Days)
1. Set up PostgreSQL database
2. Get Twitter API credentials
3. Test ingestion pipeline
4. Deploy to Render/AWS

### Short Term (Weeks)
1. Add Telegram bot ingestion
2. Build verification scoring algorithm
3. Camera partnership outreach
4. Mobile app (React Native)

### Long Term (Months)
1. Government partnership negotiations
2. AI/ML verification microservices
3. Satellite detection integration
4. Regional expansion (Oman, Kuwait, etc.)

## Government Pitch Strategy

**Value Proposition:**
> "We provide a citizen-verification layer that reduces false alarms and increases public trust. You plug in your unclassified alert stream, we combine it with ground truth from cameras and citizens."

**What's in it for them:**
- Reduced FUD and panic from social media
- Verified ground truth from multiple sources
- Public dashboard builds trust
- Open source = transparency

**What's in it for us:**
- Legitimacy
- Access to official early warning data
- Funding/support
- Real impact

## Running It

```bash
# 1. Database
psql gulfwatch -f backend/schema.sql

# 2. Backend
cd backend
cp .env.example .env
# Edit .env with credentials
npm install
npm run dev

# 3. Frontend
cd frontend
cp .env.example .env
# Add Mapbox token
npm install
npm run dev

# 4. Open http://localhost:3000
```

## Questions for You

1. **Scope:** Start with Dubai only, or multi-region from day one?
2. **Twitter API:** Do you have access or need to apply?
3. **Hosting:** Render (easy) or AWS Dubai region (faster)?
4. **Government contacts:** Anyone in Dubai Police/Civil Defense we can approach?
5. **Funding:** Self-funded initially, or seek investment/grants?

This is the foundation. Government partnerships will make it powerful. But the citizen verification layer has standalone value — even without official sensors, filtering fake news and confirming real events is useful.

Want me to continue building any specific part?
