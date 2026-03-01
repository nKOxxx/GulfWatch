# Gulf Watch - Environment Setup

## Quick Start

### 1. Database Setup

```bash
# Install PostgreSQL with PostGIS
brew install postgresql postgis

# Create database
createdb gulfwatch
psql gulfwatch -f backend/schema.sql
```

### 2. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials

npm install
npm run dev
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Data Sources

### Twitter API
1. Apply for developer account at https://developer.twitter.com
2. Create a project and app
3. Generate Bearer Token
4. Add to .env: `TWITTER_BEARER_TOKEN=...`

### Camera Partnerships
Use the API to register new partnerships:
```bash
curl -X POST http://localhost:3001/api/sources/partnerships \
  -H "Content-Type: application/json" \
  -d '{
    "organizationName": "Dubai Mall Security",
    "organizationType": "private",
    "contactEmail": "security@dubaimall.ae",
    "cameraCount": 50,
    "regions": ["DXB"]
  }'
```

## Architecture Notes

- **Backend**: Node.js + Express + PostgreSQL/PostGIS + Redis
- **Frontend**: React + Mapbox (for geospatial visualization)
- **Real-time**: WebSocket for live alerts
- **Queue**: BullMQ for background processing
- **AI/ML**: Python microservices for image/video verification (future)

## Deployment

Recommended: Render, Railway, or AWS (Dubai region for low latency)

```bash
# Docker build
docker build -t gulf-watch .
docker run -p 3001:3001 --env-file .env gulf-watch
```
