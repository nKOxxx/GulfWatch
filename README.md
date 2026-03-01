# Gulf Watch ⚠️

> **Verification-First Intelligence for the Arabian Gulf**
> 
> ⚠️ **CRITICAL: This system prioritizes accuracy over speed to prevent misinformation.**
> 
> In compliance with UAE and Gulf cybercrime laws, Gulf Watch:
> - ✅ Only publishes verified or multi-sourced reports
> - ✅ Shows source attribution for every incident
> - ✅ Displays confidence scores (unconfirmed/probable/likely/confirmed)
> - ✅ Never publishes single-source rumors
> - ✅ Prioritizes official sources over social media
> 
> **False information carries criminal penalties in the UAE. This tool is designed to combat, not spread, misinformation.**
> 
> [Read our Verification Philosophy →](VERIFICATION_PHILOSOPHY.md)

---

# Gulf Watch

**Location-based threat intelligence and verification platform for the Arabian Gulf.**

## Vision

A real-time situational awareness system that aggregates, verifies, and distributes threat information based on user location. Designed for civil defense with government and private camera partnership integration as the end-state.

## Core Principles

1. **Location-First** — Users select their region (Dubai, Abu Dhabi, Bahrain, Qatar, etc.)
2. **Verification-First** — Every piece of data is scored on reliability
3. **Partnership-Ready** — Architecture designed for government/private camera integration
4. **Open Source** — Transparency builds trust

---

## 🇦🇪 UAE Official Sources (Single Source of Truth)

These verified government accounts are treated as **authoritative sources** requiring no cross-verification:

### Federal Government
| Account | Platform | Type |
|---------|----------|------|
| [@uaegov](https://twitter.com/uaegov) | Twitter/X | Federal Government |
| [@WAMnews](https://twitter.com/WAMnews) | Twitter/X | State Media |
| [@moiuae](https://twitter.com/moiuae) | Twitter/X | Ministry of Interior |
| [@uae_cd](https://twitter.com/uae_cd) | Twitter/X | Civil Defense |
| [@ncema_uae](https://twitter.com/ncema_uae) | Twitter/X | Emergency Management |

### Rulers
| Account | Platform | Type |
|---------|----------|------|
| [@mohamedbinzayed](https://twitter.com/mohamedbinzayed) | Twitter/X | President of UAE |
| [@hhshkmohd](https://twitter.com/hhshkmohd) | Twitter/X | Dubai Ruler |
| [@sultanalqasimi](https://twitter.com/sultanalqasimi) | Twitter/X | Sharjah Ruler |

### Dubai
| Account | Platform | Type |
|---------|----------|------|
| [@dubaipolicehq](https://twitter.com/dubaipolicehq) | Twitter/X | Police |
| [@dubai_civildef](https://twitter.com/dubai_civildef) | Twitter/X | Civil Defense |
| [@dxbmediaoffice](https://twitter.com/dxbmediaoffice) | Twitter/X | Media Office |

### Abu Dhabi
| Account | Platform | Type |
|---------|----------|------|
| [@ad_policehq](https://twitter.com/ad_policehq) | Twitter/X | Police |
| [@abudhabi_gov](https://twitter.com/abudhabi_gov) | Twitter/X | Government |
| [@admediaoffice](https://twitter.com/admediaoffice) | Twitter/X | Media Office |

### Verified Media (Require 2+ sources)
| Account | Platform | Type |
|---------|----------|------|
| [@gulf_news](https://twitter.com/gulf_news) | Twitter/X | Media |
| [@thenationaluae](https://twitter.com/thenationaluae) | Twitter/X | Media |
| [@khaleejtimes](https://twitter.com/khaleejtimes) | Twitter/X | Media |

**[Full list in official-sources.yaml →](config/official-sources.yaml)**

---

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
