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
| Account | Twitter/X | Instagram | Type |
|---------|-----------|-----------|------|
| UAE Government | [@uaegov](https://twitter.com/uaegov) | [@uaegov](https://instagram.com/uaegov) | Federal Government |
| WAM News Agency | [@WAMnews](https://twitter.com/WAMnews) | [@wam_news](https://instagram.com/wam_news) | State Media |
| Ministry of Interior | [@moiuae](https://twitter.com/moiuae) | — | Security |
| UAE Civil Defense | [@uae_cd](https://twitter.com/uae_cd) | — | Civil Defense |
| NCEMA | [@ncema_uae](https://twitter.com/ncema_uae) | — | Emergency Management |

### Rulers
| Account | Twitter/X | Instagram | Type |
|---------|-----------|-----------|------|
| HH Sheikh Mohamed bin Zayed | [@mohamedbinzayed](https://twitter.com/mohamedbinzayed) | [@mohamedbinzayed](https://instagram.com/mohamedbinzayed) | President of UAE |
| HH Sheikh Mohammed bin Rashid | [@hhshkmohd](https://twitter.com/hhshkmohd) | [@hhshkmohd](https://instagram.com/hhshkmohd) | Dubai Ruler |
| HH Sheikh Dr. Sultan Al Qasimi | [@sultanalqasimi](https://twitter.com/sultanalqasimi) | — | Sharjah Ruler |

### Dubai
| Account | Twitter/X | Instagram | Type |
|---------|-----------|-----------|------|
| Dubai Police | [@dubaipolicehq](https://twitter.com/dubaipolicehq) | — | Police |
| Dubai Civil Defense | [@dubai_civildef](https://twitter.com/dubai_civildef) | — | Civil Defense |
| Dubai Media Office | [@dxbmediaoffice](https://twitter.com/dxbmediaoffice) | — | Media Office |

### Abu Dhabi
| Account | Twitter/X | Instagram | Type |
|---------|-----------|-----------|------|
| Abu Dhabi Police | [@ad_policehq](https://twitter.com/ad_policehq) | — | Police |
| Abu Dhabi Government | [@abudhabi_gov](https://twitter.com/abudhabi_gov) | — | Government |
| Abu Dhabi Media Office | [@admediaoffice](https://twitter.com/admediaoffice) | — | Media Office |

### Verified Media (Require 2+ sources)
| Account | Twitter/X | Instagram | Type |
|---------|-----------|-----------|------|
| Gulf News | [@gulf_news](https://twitter.com/gulf_news) | [@gulf_news](https://instagram.com/gulf_news) | Media |
| The National | [@thenationaluae](https://twitter.com/thenationaluae) | [@thenationaluae](https://instagram.com/thenationaluae) | Media |
| Khaleej Times | [@khaleejtimes](https://twitter.com/khaleejtimes) | [@khaleejtimes](https://instagram.com/khaleejtimes) | Media |

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
