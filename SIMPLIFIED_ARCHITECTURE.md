# Gulf Watch - Simplified Architecture

## Current Problems
1. Twitter API v2 requires paid credits ($$$)
2. Complex database schema causing deployment issues
3. Over-engineered verification pipeline
4. Render free tier too slow for rapid iteration

## WorldMonitor Approach (Working)
- RSS feeds only (no APIs)
- Simple aggregation
- Display raw feeds with basic categorization
- Local processing where possible

## Simplified Gulf Watch v2

### Option 1: Static JSON + RSS Frontend (Vercel Only)
- Pre-fetch RSS feeds at build time
- Generate static JSON with incidents
- Deploy to Vercel (fast, free)
- No backend database needed
- Update via GitHub Actions every hour

### Option 2: Serverless Functions (Vercel Edge)
- Edge functions fetch RSS on-demand
- Cache for 5 minutes
- Return JSON directly
- No persistent database
- Simple, fast, reliable

### Option 3: Use WorldMonitor Data
- WorldMonitor already has Middle East feeds working
- Fork their approach
- Focus on Gulf region only
- Strip out global features

## Recommended: Option 1 (Fastest to Deploy)

1. Create GitHub Action to run every hour
2. Fetch 20+ RSS feeds (Reuters, BBC, Al Jazeera, etc.)
3. Parse for threat keywords
4. Generate incidents.json
5. Commit to repo
6. Vercel auto-deploys
7. Frontend reads static JSON

**Pros:**
- Zero backend maintenance
- Free (GitHub + Vercel)
- Fast deploys
- Reliable

**Cons:**
- 1-hour delay max
- No real-time updates
- No user subscriptions

## Gulf-Specific RSS Feeds to Use

```yaml
# Tier 1 - International
- Reuters Middle East: https://www.reuters.com/news/archive/middleeast.rss
- BBC Middle East: http://feeds.bbci.co.uk/news/world/middle_east/rss.xml
- Al Jazeera: https://www.aljazeera.com/xml/rss/all.xml
- AP Middle East: https://apnews.com/hub/middle-east.rss

# Tier 2 - Regional
- The National (UAE): https://www.thenationalnews.com/arc/outboundfeeds/rss/
- Gulf News: https://gulfnews.com/rss
- Khaleej Times: https://www.khaleejtimes.com/arc/outboundfeeds/rss/
- Arab News: https://www.arabnews.com/rss.xml
- Times of Israel: https://www.timesofisrael.com/feed/
- Jerusalem Post: https://www.jpost.com/Rss/RssFeedsHeadlines.aspx

# Tier 3 - Defense/Security
- Defense News: https://www.defensenews.com/arc/outboundfeeds/rss/
- Jane's Defence Weekly: https://www.janes.com/feeds/news
- Breaking Defense: https://breakingdefense.com/feed/
```

## Implementation Plan

### Step 1: Create RSS Fetcher Script
```python
# scripts/fetch_rss.py
import feedparser
import json
from datetime import datetime

FEEDS = [...]  # List above
KEYWORDS = ['missile', 'drone', 'attack', 'explosion', 'air defense', ...]

def fetch_all():
    incidents = []
    for feed in FEEDS:
        entries = feedparser.parse(feed['url']).entries[:10]
        for entry in entries:
            if any(k in entry.title.lower() for k in KEYWORDS):
                incidents.append({
                    'title': entry.title,
                    'source': feed['name'],
                    'url': entry.link,
                    'published': entry.published,
                    'location': extract_location(entry.title)
                })
    
    with open('public/incidents.json', 'w') as f:
        json.dump(incidents, f, indent=2)

if __name__ == '__main__':
    fetch_all()
```

### Step 2: GitHub Action
```yaml
# .github/workflows/update-feeds.yml
name: Update RSS Feeds
on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install feedparser
      - run: python scripts/fetch_rss.py
      - uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: 'Update RSS feeds'
```

### Step 3: Frontend
- Read `/incidents.json` from public folder
- Display on map
- No backend needed

## Decision

**Recommend Option 1** - Static JSON approach:
- Deploy in 30 minutes
- No Render complexity
- Reliable updates every hour
- Free forever

Want me to implement this simplified version?
