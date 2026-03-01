# Gulf Watch Intelligence Pipeline

## Core Concept

**Ingest → Verify → Distribute**

No fancy UI. Just reliable information flow.

## Data Sources

### 1. Twitter/X Stream
**Keywords to track:**
```
dubai, abu dhabi, uae, bahrain, qatar, saudi
explosion, blast, boom, attack, strike, missile, drone
siren, air raid, alert, emergency
palm jumeirah, burj khalifa, downtown, marina, creek harbour
iran, israel, war, conflict, defense, interceptor
انفجار, صاروخ, طائرة, مسيرة, إنذار, دبي
```

**Source Credibility Scoring:**
- Verified account: +50 points
- 10k+ followers: +20 points
- 100k+ followers: +40 points
- 1M+ followers: +60 points
- Media/journalist bio: +30 points
- History of accurate reports: +40 points
- Random account: 0 points

### 2. News Sources
**High credibility (auto-verified):**
- Reuters, AP, AFP, BBC, Al Jazeera
- Local: Gulf News, Khaleej Times, The National
- Official: WAM (UAE), BNA (Bahrain), QNA (Qatar)

**Medium credibility:**
- Regional outlets, verified blogs

### 3. Telegram Channels
- Dubai Civil Defence
- UAE official channels
- Verified community channels

## Verification Algorithm

```python
def verify_event(reports):
    """
    Reports: list of {source, location, time, text, credibility_score}
    """
    
    # Group by location (within 2km radius)
    location_clusters = cluster_by_location(reports, radius_km=2)
    
    for cluster in location_clusters:
        # Calculate verification score
        unique_sources = len(set(r['source'] for r in cluster))
        total_credibility = sum(r['credibility_score'] for r in cluster)
        time_spread = max(r['time'] for r in cluster) - min(r['time'] for r in cluster)
        
        # Verification levels
        if total_credibility >= 200:  # e.g., Reuters + 2 verified accounts
            status = "CONFIRMED"
        elif unique_sources >= 10:
            status = "CONFIRMED"
        elif unique_sources >= 5 and total_credibility >= 100:
            status = "LIKELY"
        elif unique_sources >= 2:
            status = "PROBABLE"
        else:
            status = "UNCONFIRMED"
        
        # Extract location from text if not geotagged
        location = extract_location(cluster[0]['text'])
        
        yield {
            'status': status,
            'location': location,
            'reports_count': unique_sources,
            'credibility_score': total_credibility,
            'first_seen': min(r['time'] for r in cluster),
            'sources': cluster
        }
```

## Distribution Logic

```python
def should_alert_user(user_location, event, radius_km=10):
    """Check if user should be notified"""
    distance = calculate_distance(user_location, event['location'])
    
    if distance <= 5 and event['status'] in ['CONFIRMED', 'LIKELY']:
        return True  # Immediate alert
    elif distance <= radius_km and event['status'] == 'CONFIRMED':
        return True  # Standard alert
    elif distance <= 20 and event['status'] == 'CONFIRMED' and is_high_severity(event):
        return True  # Major event, wider radius
    
    return False
```

## MVP Implementation Plan

### Phase 1: Twitter Ingestion (2 hours)
- [ ] Twitter API connection
- [ ] Keyword stream
- [ ] Basic credibility scoring
- [ ] Store in database

### Phase 2: Verification Engine (2 hours)
- [ ] Location clustering
- [ ] Source scoring
- [ ] Status calculation
- [ ] Deduplication

### Phase 3: Simple UI (1 hour)
- [ ] List view: Confirmed events only
- [ ] Location filter
- [ ] Report button (adds to verification pool)

### Phase 4: Distribution (1 hour)
- [ ] Push notifications
- [ ] Location-based filtering
- [ ] Telegram bot

## Database Schema

```sql
-- Raw reports from all sources
CREATE TABLE reports (
    id UUID PRIMARY KEY,
    source_type TEXT, -- 'twitter', 'news', 'telegram', 'user'
    source_id TEXT,   -- username, outlet name
    source_credibility INTEGER,
    content TEXT,
    media_urls TEXT[],
    location_text TEXT,
    location_lat FLOAT,
    location_lng FLOAT,
    created_at TIMESTAMP,
    raw_data JSONB
);

-- Verified events
CREATE TABLE events (
    id UUID PRIMARY KEY,
    status TEXT, -- 'UNCONFIRMED', 'PROBABLE', 'LIKELY', 'CONFIRMED'
    event_type TEXT, -- 'explosion', 'interceptor', 'siren'
    location_lat FLOAT,
    location_lng FLOAT,
    location_name TEXT,
    first_reported TIMESTAMP,
    last_updated TIMESTAMP,
    reports_count INTEGER,
    total_credibility INTEGER,
    description TEXT
);

-- Link reports to events
CREATE TABLE event_reports (
    event_id UUID REFERENCES events(id),
    report_id UUID REFERENCES reports(id)
);

-- User subscriptions
CREATE TABLE subscriptions (
    user_id TEXT,
    location_lat FLOAT,
    location_lng FLOAT,
    alert_radius_km INTEGER DEFAULT 10,
    min_severity TEXT DEFAULT 'LIKELY'
);
```

## Next Steps

1. **Build ingestion service** - Twitter stream + news scrapers
2. **Test verification** - Run on today's Dubai incidents
3. **Simple output** - Just a list of verified events
4. **Then** make it pretty

Want me to start building the ingestion pipeline?
