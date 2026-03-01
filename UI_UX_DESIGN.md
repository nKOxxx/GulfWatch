# Gulf Watch UI/UX Design

## Core Principle: "Am I Safe?" First

User opens app with ONE question: **"Is there a threat near me?"**

Answer in < 2 seconds, then details if they want them.

---

## Screen 1: Status Dashboard (Main View)

```
┌─────────────────────────────────────┐
│  ⚠️ 2 ACTIVE INCIDENTS      🔔 🗺️ │  ← Header (always visible)
├─────────────────────────────────────┤
│                                     │
│    ┌─────────────────────────┐     │
│    │                         │     │
│    │    [MINIMAL MAP]        │     │  ← Gulf region
│    │    • Red = Active       │     │     • = your location
│    │    • Yellow = Watch     │     │     🔴 = incident
│    │    • Green = Clear      │     │
│    │                         │     │
│    └─────────────────────────┘     │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ 🔴  NEARBY: Dubai Marina      │  │  ← CLOSEST threat
│  │     Confirmed | 12 min ago    │  │     (tap for details)
│  │     ⚠️ Air defense active     │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ 🟡  WATCH: Abu Dhabi          │  │  ← Secondary
│  │     Reports unconfirmed       │  │
│  └───────────────────────────────┘  │
│                                     │
│     [View All Incidents →]          │
│                                     │
├─────────────────────────────────────┤
│ 🏛️ OFFICIAL | 📰 NEWS | ✈️ TRACKING │  ← Bottom tabs
└─────────────────────────────────────┘
```

### Design Rules:
- **NO clutter** - Only show ACTIVE threats by default
- **Distance prioritized** - Closest to user first
- **Status color-coded** - Red/Orange/Yellow/Green
- **One-tap details** - Everything expandable

---

## Screen 2: Incident Detail (Expanded)

```
┌─────────────────────────────────────┐
│ ← Back                    Share 📤  │
├─────────────────────────────────────┤
│                                     │
│  🔴 CONFIRMED                       │
│  Air Defense Interception           │
│  Dubai Marina, UAE                  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │     [MAP - incident zoom]     │  │
│  │         • ← You are here      │  │
│  │         🔴 ← Incident         │  │
│  │         15 km away            │  │
│  └───────────────────────────────┘  │
│                                     │
│  📍 YOUR LOCATION                   │
│  Dubai Downtown                     │
│  15 km from incident                │
│  🟢 You are NOT in affected zone    │
│                                     │
├─────────────────────────────────────┤
│  📋 WHAT HAPPENED                   │
├─────────────────────────────────────┤
│  17:43 - Air defense systems        │
│          activated over Dubai       │
│                                     │
│  Source: @WAMnews (Official)        │
│  + 12 other sources                 │
│                                     │
│  [View all sources →]               │
│                                     │
├─────────────────────────────────────┤
│  🏛️ OFFICIAL GUIDANCE               │
├─────────────────────────────────────┤
│  @uae_cd (Civil Defense):           │
│  "Stay indoors. Away from windows.  │
│   Follow official channels only."   │
│                                     │
│  17:45 • Official Account           │
│                                     │
├─────────────────────────────────────┤
│  📡 LIVE TRACKING                   │
├─────────────────────────────────────┤
│  ✈️ Aircraft:     Normal traffic    │
│  🚢 Ships:        No restrictions   │
│  🛸 Drones:       Intercepted       │
│                                     │
│  [Open Live Map →]                  │
│                                     │
├─────────────────────────────────────┤
│  📰 RELATED NEWS                    │
├─────────────────────────────────────┤
│  Reuters: "UAE intercepts..."       │
│  17:50 • Verified Media             │
│                                     │
│  Al Arabiya: "Dubai residents..."   │
│  17:52 • Verified Media             │
│                                     │
└─────────────────────────────────────┘
```

### Sections (collapsible, default: first 2 expanded):
1. **What Happened** (always open)
2. **Official Guidance** (always open)
3. **Your Location Status** (always open)
4. Live Tracking (collapsed)
5. Related News (collapsed)
6. All Sources (collapsed)

---

## Screen 3: Live Tracking Map

```
┌─────────────────────────────────────┐
│ ← Back              Filters ⚙️      │
├─────────────────────────────────────┤
│                                     │
│  ┌───────────────────────────────┐  │
│  │                               │  │
│  │      [FULL INTERACTIVE MAP]   │  │
│  │                               │  │
│  │    Layer controls:            │  │
│  │    [✈️] [🚢] [🛸] [💥] [📡]   │  │
│  │                               │  │
│  │    ✈️ = Aircraft              │  │
│  │    🚢 = Ships                 │  │
│  │    🛸 = Drones/UAVs           │  │
│  │    💥 = Impact sites          │  │
│  │    📡 = Air defense           │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                                     │
│  Legend:                            │
│  🔴 Active incident    🟡 Watch     │
│  🟢 Safe zone          ⏺️ You       │
│                                     │
└─────────────────────────────────────┘
```

### Filter Defaults:
- ✅ Air defense (always on)
- ✅ Impact sites (always on)
- ⚠️ Drones (on during active threat)
- ⏸️ Ships (off by default)
- ⏸️ Aircraft (off by default)

---

## Screen 4: Official Statements Feed

```
┌─────────────────────────────────────┐
│  🏛️ OFFICIAL STATEMENTS             │
├─────────────────────────────────────┤
│                                     │
│  📍 UAE                              │
│  ┌───────────────────────────────┐  │
│  │ @WAMnews                        │  │
│  │ "Air defense systems..."        │  │
│  │                                 │  │
│  │ 🕐 17:43 | Verified Official    │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ @uae_cd                         │  │
│  │ "Stay indoors, away from..."    │  │
│  │                                 │  │
│  │ 🕐 17:45 | Civil Defense        │  │
│  └───────────────────────────────┘  │
│                                     │
│  📍 Saudi Arabia                     │
│  ┌───────────────────────────────┐  │
│  │ @SaudiPressAgency               │  │
│  │ "Monitoring situation..."       │  │
│  │                                 │  │
│  │ 🕐 17:50 | Official Media       │  │
│  └───────────────────────────────┘  │
│                                     │
│  [Filter by country ▼]              │
│                                     │
└─────────────────────────────────────┘
```

### Priority Order:
1. Your location's official statements
2. Neighboring countries
3. Regional powers
4. International

---

## Data Hierarchy (What Shows When)

### Priority 1: CRITICAL (Always Visible)
- Active incidents near user
- Official guidance for active threat
- Your safety status

### Priority 2: IMPORTANT (Default Collapsed)
- Distant incidents
- Unconfirmed reports
- Related news

### Priority 3: DETAIL (Tap to Expand)
- All sources list
- Ship positions
- Aircraft tracking
- Historical data

---

## Color System

| Color | Meaning | Use |
|-------|---------|-----|
| 🔴 Red | Confirmed active threat | Incidents, warnings |
| 🟠 Orange | Probable/Likely | Reports gathering |
| 🟡 Yellow | Watch/Unconfirmed | Monitoring |
| 🟢 Green | Safe/Clear | No threat, safe zones |
| 🔵 Blue | Official | Government sources |
| ⚪ Gray | Inactive | Resolved incidents |

---

## Typography & Spacing

### Font Sizes:
- **Status**: 48px (big, scannable)
- **Incident title**: 24px
- **Body**: 16px
- **Metadata**: 14px (time, source)

### Spacing:
- Generous whitespace
- Cards with clear separation
- 16px padding minimum
- No walls of text

---

## Key Principles

### 1. Progressive Disclosure
- Show ONLY what user needs NOW
- Details one tap away
- Never overwhelm

### 2. Location Context
- Always show "where am I vs incident"
- Distance prominently displayed
- Safe/not safe immediately clear

### 3. Official First
- Official statements above news
- Government sources clearly marked
- Unverified clearly labeled

### 4. Actionable
- Not just "what happened" but "what do I do"
- Official guidance prominent
- Clear safety instructions

---

## Mobile-First

- All screens work on phone
- Thumb-friendly tap targets (min 44px)
- Bottom navigation (reachable)
- Swipe between views

---

## Notifications (Push)

```
🔴 CONFIRMED: Air defense active
Dubai Marina - 15 km from you

[View]  [I'm Safe]
```

Only push for:
- Confirmed incidents in your area
- Official guidance updates
- All-clear announcements

---

## Summary: Design Philosophy

| Bad (Overwhelming) | Good (Focused) |
|-------------------|----------------|
| Show everything | Show what matters |
| Speed-first | Clarity-first |
| Information dump | Progressive disclosure |
| News feed | Safety tool |
| Global view | Your location first |

**User should know their safety status in 2 seconds.**
