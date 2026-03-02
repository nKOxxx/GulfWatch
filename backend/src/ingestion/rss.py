"""
RSS News Feed Ingestion for Gulf Watch
Monitors news outlets via RSS feeds - no API limits
"""
import os
import re
import feedparser
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import httpx
from sqlalchemy.orm import Session

from models import get_db, RawReport, Incident, Source, RawReportCRUD, SourceCRUD

class RSSIngestion:
    """Ingest news from RSS feeds"""
    
    # RSS feeds for major news outlets (Gulf region focus)
    NEWS_FEEDS = [
        # Tier 1 - International
        {'name': 'Reuters', 'url': 'https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best', 'country': 'International', 'credibility': 95},
        {'name': 'Reuters Middle East', 'url': 'https://www.reuters.com/news/archive/middleeast.rss', 'country': 'Middle East', 'credibility': 95},
        {'name': 'BBC News', 'url': 'http://feeds.bbci.co.uk/news/rss.xml', 'country': 'International', 'credibility': 95},
        {'name': 'BBC Middle East', 'url': 'http://feeds.bbci.co.uk/news/world/middle_east/rss.xml', 'country': 'Middle East', 'credibility': 95},
        
        # Tier 2 - Gulf Regional
        {'name': 'Al Jazeera', 'url': 'https://www.aljazeera.com/xml/rss/all.xml', 'country': 'Qatar', 'credibility': 90},
        {'name': 'Al Jazeera Middle East', 'url': 'https://www.aljazeera.com/xml/rss/all.xml', 'country': 'Middle East', 'credibility': 90},
        {'name': 'The National UAE', 'url': 'https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml', 'country': 'UAE', 'credibility': 85},
        {'name': 'Gulf News', 'url': 'https://gulfnews.com/rss', 'country': 'UAE', 'credibility': 85},
        {'name': 'Khaleej Times', 'url': 'https://www.khaleejtimes.com/arc/outboundfeeds/rss/?outputType=xml', 'country': 'UAE', 'credibility': 80},
        {'name': 'Arab News', 'url': 'https://www.arabnews.com/rss.xml', 'country': 'Saudi Arabia', 'credibility': 80},
        
        # Defense/Security
        {'name': 'Defense News', 'url': 'https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml', 'country': 'International', 'credibility': 90},
        {'name': 'Jane\'s Defence', 'url': 'https://www.janes.com/feeds/news', 'country': 'International', 'credibility': 95},
        
        # Israel sources
        {'name': 'Times of Israel', 'url': 'https://www.timesofisrael.com/feed/', 'country': 'Israel', 'credibility': 85},
        {'name': 'Jerusalem Post', 'url': 'https://www.jpost.com/Rss/RssFeedsHeadlines.aspx', 'country': 'Israel', 'credibility': 85},
    ]
    
    # Keywords that indicate threats/incidents
    THREAT_KEYWORDS = [
        'explosion', 'blast', 'attack', 'missile', 'drone', 'uav',
        'air defense', 'interceptor', 'siren', 'alert', 'emergency',
        'strike', 'impact', 'exploded', 'smoke', 'fire', 'warning',
        'حرب', 'هجوم', 'صاروخ', 'طائرة', 'مسيرة', 'انفجار', 'تحذير'
    ]
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def is_threat_related(self, text: str) -> bool:
        """Check if article is threat-related"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.THREAT_KEYWORDS)
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from text"""
        # Gulf cities mapping
        cities = {
            'dubai': 'Dubai', 'abu dhabi': 'Abu Dhabi', 'sharjah': 'Sharjah',
            'riyadh': 'Riyadh', 'jeddah': 'Jeddah', 'mecca': 'Mecca', 'medina': 'Medina',
            'doha': 'Doha', 'manama': 'Manama', 'kuwait city': 'Kuwait City',
            'muscat': 'Muscat', 'tel aviv': 'Tel Aviv', 'jerusalem': 'Jerusalem',
            'gaza': 'Gaza', 'beirut': 'Beirut', 'baghdad': 'Baghdad',
            'uae': 'UAE', 'saudi': 'Saudi Arabia', 'qatar': 'Qatar',
            'bahrain': 'Bahrain', 'kuwait': 'Kuwait', 'oman': 'Oman',
            'israel': 'Israel', 'palestine': 'Palestine', 'gulf': 'Gulf Region'
        }
        
        text_lower = text.lower()
        for city_key, city_name in cities.items():
            if city_key in text_lower:
                return city_name
        return None
    
    def get_or_create_source(self, feed_info: Dict) -> Source:
        """Get or create source from RSS feed"""
        handle = f"@{feed_info['name'].lower().replace(' ', '_')}"
        
        source = SourceCRUD.get_by_handle(self.db, handle, "rss")
        
        if not source:
            source = Source(
                name=feed_info['name'],
                handle=handle,
                platform="rss",
                source_type="news_media",
                credibility_score=feed_info['credibility'],
                is_official=True if feed_info['credibility'] >= 90 else False,
                is_verified=True,
                country=feed_info['country']
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
            print(f"✅ Created RSS source: {feed_info['name']}")
        
        return source
    
    def process_feed_item(self, entry, source: Source) -> Optional[RawReport]:
        """Process RSS feed item into raw report"""
        title = entry.get('title', '')
        summary = entry.get('summary', '')
        link = entry.get('link', '')
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        
        full_text = f"{title} {summary}"
        
        # Skip if not threat-related
        if not self.is_threat_related(full_text):
            return None
        
        # Check if already processed
        existing = self.db.query(RawReport).filter(
            RawReport.external_id == link
        ).first()
        
        if existing:
            return None
        
        # Parse timestamp
        if published:
            posted_at = datetime(*published[:6])
        else:
            posted_at = datetime.utcnow()
        
        # Extract location
        location_name = self.extract_location(full_text)
        
        # Create raw report
        raw_report = RawReport(
            source_id=source.id,
            external_id=link,
            content=full_text,
            posted_at=posted_at,
            location_text=location_name,
            source_credibility=source.credibility_score,
            is_verified_source=source.is_verified,
            raw_data={
                'title': title,
                'link': link,
                'source_name': source.name
            },
            processed=False
        )
        
        self.db.add(raw_report)
        self.db.commit()
        self.db.refresh(raw_report)
        
        print(f"✅ Created report from {source.name}: {title[:50]}...")
        return raw_report
    
    def ingest_feed(self, feed_info: Dict) -> int:
        """Ingest single RSS feed"""
        print(f"\n📡 Fetching {feed_info['name']}...")
        
        try:
            # Parse feed
            feed = feedparser.parse(feed_info['url'])
            
            if hasattr(feed, 'bozo_exception'):
                print(f"   ⚠️ Feed warning: {feed.bozo_exception}")
            
            # Get or create source
            source = self.get_or_create_source(feed_info)
            
            # Process entries from last 24h
            new_reports = 0
            cutoff = datetime.utcnow() - timedelta(hours=24)
            
            for entry in feed.entries[:20]:  # Process last 20 entries
                published = entry.get('published_parsed')
                if published:
                    entry_time = datetime(*published[:6])
                    if entry_time < cutoff:
                        continue
                
                report = self.process_feed_item(entry, source)
                if report:
                    new_reports += 1
            
            print(f"   Found {new_reports} threat-related articles")
            return new_reports
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return 0
    
    def run_ingestion(self) -> Dict:
        """Run RSS ingestion for all feeds"""
        print("🔄 Starting RSS News Ingestion")
        print("=" * 50)
        
        total_new = 0
        errors = 0
        results = {}
        
        for feed in self.NEWS_FEEDS:
            try:
                count = self.ingest_feed(feed)
                total_new += count
                results[feed['name']] = {"new_reports": count}
            except Exception as e:
                errors += 1
                results[feed['name']] = {"error": str(e)}
        
        summary = {
            "status": "success",
            "total_new_reports": total_new,
            "errors": errors,
            "feeds_checked": len(self.NEWS_FEEDS),
            "by_feed": results
        }
        
        print(f"\n✅ RSS Ingestion complete!")
        print(f"   Total new reports: {total_new}")
        print(f"   Errors: {errors}")
        
        return summary
    
    def backfill_last_24h(self) -> Dict:
        """Backfill last 24 hours from RSS feeds"""
        return self.run_ingestion()
