# Gulf Watch

**Location-based threat intelligence and verification platform for the Arabian Gulf.**

## Vision

A real-time situational awareness system that aggregates, verifies, and distributes threat information based on user location. Designed for civil defense with government and private camera partnership integration as the end-state.

## Core Principles

1. **Location-First** — Users select their region (Dubai, Abu Dhabi, Bahrain, Qatar, etc.)
2. **Verification-First** — Every piece of data is scored on reliability
3. **Partnership-Ready** — Architecture designed for government/private camera integration
4. **Open Source** — Transparency builds trust

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GULF WATCH PLATFORM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   INGESTION  │  │ VERIFICATION │  │ DISTRIBUTION │      │
│  │    LAYER     │  │    ENGINE    │  │    LAYER     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           ▼                                │
│              ┌──────────────────────┐                      │
│              │   INTELLIGENCE HUB   │                      │
│              │  (Location-Based)    │                      │
│              └──────────┬───────────┘                      │
│                         │                                  │
│         ┌───────────────┼───────────────┐                  │
│         ▼               ▼               ▼                  │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐              │
│    │ Dubai   │    │ Bahrain │    │  Doha   │              │
│    │  Hub    │    │  Hub    │    │  Hub    │              │
│    └─────────┘    └─────────┘    └─────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Sources (Current)

- Social media (Twitter/X, Telegram)
- Local news feeds
- ADS-B aviation data
- Public cameras (where accessible)
- Seismic/acoustic sensors

## Data Sources (Future - Partnerships)

- Government security cameras
- Military early warning systems
- Private critical infrastructure cameras
- Satellite detection feeds

## Tech Stack

- **Backend:** Node.js + Express + TypeScript
- **Database:** PostgreSQL + PostGIS (geospatial)
- **Cache:** Redis
- **Frontend:** React + TypeScript + Mapbox
- **AI/ML:** Python microservices for verification
- **Infrastructure:** Docker + Kubernetes

## Status

🚧 Under Construction

## License

MIT - Government-friendly open source
