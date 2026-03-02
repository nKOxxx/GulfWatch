"""
Twitter/X API Integration for Gulf Watch
Monitors official Gulf sources and creates incidents
"""

import os
import re
from datetime import datetime
from typing import Optional, List, Dict
import httpx
from sqlalchemy.orm import Session

from models import (
    get_db, RawReport, Incident, Source,
    RawReportCRUD, IncidentCRUD, SourceCRUD,
    init_database
)
from intelligence.engine import VerificationEngine, Report
from intelligence.official_sources import get_uae_official_sources

# Twitter API v2 credentials (from environment)
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')

class TwitterIngestion:
    """Ingest tweets from official Gulf sources"""
    
    BASE_URL = "https://api.twitter.com/2"
    
    # UAE Official handles to monitor
    UAE_HANDLES = [
        'WAMnews',          # WAM News Agency
        'uae_cd',           # UAE Civil Defense
        'moiuae',           # Ministry of Interior
        'ncema_uae',        # NCEMA
        'dubaipolicehq',    # Dubai Police
        'dubai_civildef',   # Dubai Civil Defense
        'ad_policehq',      # Abu Dhabi Police
        'mohamedbinzayed',  # President MBZ
        'hhshkmohd',        # Dubai Ruler MBR
    ]
    
    # Saudi Arabia Official handles
    SAUDI_HANDLES = [
        'SaudiMOI',         # Saudi Ministry of Interior
        'SaudiNews50',      # Saudi News 50 (official news)
        'SPAregions',       # Saudi Press Agency - Regions
        'spagov',           # Saudi Press Agency
        'MODA Saudi',       # Ministry of Defense
    ]
    
    # Qatar Official handles
    QATAR_HANDLES = [
        'MOIQatar',         # Qatar Ministry of Interior
        'QatarNewsAgency',  # Qatar News Agency
        'qatarembassy',     # Qatar Embassy
    ]
    
    # Bahrain Official handles
    BAHRAIN_HANDLES = [
        'BahrainNews',      # Bahrain News Agency
        'InteriorMinistry', # Bahrain Interior Ministry
        'bahrainpolice',    # Bahrain Police
    ]
    
    # Combined list for monitoring
    MONITORED_HANDLES = UAE_HANDLES + SAUDI_HANDLES + QATAR_HANDLES + BAHRAIN_HANDLES
    
    # Keywords that indicate threats/incidents
    THREAT_KEYWORDS = [
        'explosion', 'blast', 'attack', 'missile', 'drone', 'uav',
        'air defense', 'interceptor', 'siren', 'alert', 'emergency',
        'strike', 'impact', 'exploded', 'smoke', 'fire',
        'انفجار', 'صاروخ', 'طائرة', 'مسيرة', 'إنذار'
    ]
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.verification_engine = VerificationEngine()
        self.headers = {
            "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"
        } if TWITTER_BEARER_TOKEN else {}
    
    def fetch_user_tweets(self, username: str, max_results: int = 10) -> List[Dict]:
        """Fetch recent tweets from a user"""
        if not TWITTER_BEARER_TOKEN:
            print(f"⚠️ No Twitter API token, skipping @{username}")
            return []
        
        try:
            # First get user ID
            user_url = f"{self.BASE_URL}/users/by/username/{username}"
            response = httpx.get(user_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Failed to get user @{username}: {response.status_code}")
                return []
            
            user_data = response.json()
            user_id = user_data['data']['id']
            
            # Then get tweets
            tweets_url = f"{self.BASE_URL}/users/{user_id}/tweets"
            params = {
                'max_results': max_results,
                'tweet.fields': 'created_at,geo,public_metrics',
                'exclude': 'retweets,replies'
            }
            
            response = httpx.get(tweets_url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Failed to get tweets for @{username}: {response.status_code}")
                return []
            
            data = response.json()
            return data.get('data', [])
            
        except Exception as e:
            print(f"❌ Error fetching @{username}: {e}")
            return []
    
    def is_threat_related(self, text: str) -> bool:
        """Check if tweet is threat-related"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.THREAT_KEYWORDS)
    
    def extract_location(self, text: str) -> Optional[tuple]:
        """Extract location from tweet text"""
        # Use the same location extractor from verification engine
        from intelligence.engine import LocationExtractor
        extractor = LocationExtractor()
        return extractor.extract(text)
    
    def process_tweet(self, tweet: Dict, username: str) -> Optional[RawReport]:
        """Process a single tweet into a raw report"""
        text = tweet.get('text', '')
        tweet_id = tweet.get('id')
        created_at = tweet.get('created_at')
        
        # Skip if not threat-related
        if not self.is_threat_related(text):
            return None
        
        # Check if already processed
        existing = self.db.query(RawReport).filter(
            RawReport.external_id == tweet_id
        ).first()
        
        if existing:
            return None
        
        # Get source
        source = SourceCRUD.get_by_handle(self.db, f"@{username}", "twitter")
        if not source:
            print(f"⚠️ Source @{username} not found in database")
            return None
        
        # Extract location
        location_data = self.extract_location(text)
        location = None
        location_name = None
        
        if location_data:
            location_name, lat, lng = location_data
            from geoalchemy2.elements import WKTElement
            location = WKTElement(f'POINT({lng} {lat})', srid=4326)
        
        # Parse timestamp
        try:
            posted_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            posted_at = datetime.utcnow()
        
        # Create raw report
        raw_report = RawReport(
            source_id=source.id,
            external_id=tweet_id,
            content=text,
            posted_at=posted_at,
            location_text=location_name,
            location=location,
            source_credibility=source.credibility_score,
            follower_count=source.follower_count,
            is_verified_source=source.is_verified,
            raw_data=tweet,
            processed=False
        )
        
        self.db.add(raw_report)
        self.db.commit()
        self.db.refresh(raw_report)
        
        print(f"✅ Created raw report from @{username}: {text[:50]}...")
        return raw_report
    
    def run_ingestion(self):
        """Run full ingestion cycle"""
        print("🔄 Starting Twitter ingestion...")
        print(f"   Monitoring {len(self.MONITORED_HANDLES)} official accounts")
        print(f"   - UAE: {len(self.UAE_HANDLES)} accounts")
        print(f"   - Saudi Arabia: {len(self.SAUDI_HANDLES)} accounts")
        print(f"   - Qatar: {len(self.QATAR_HANDLES)} accounts")
        print(f"   - Bahrain: {len(self.BAHRAIN_HANDLES)} accounts")
        
        total_reports = 0
        
        for username in self.MONITORED_HANDLES:
            print(f"\n📡 Checking @{username}...")
            tweets = self.fetch_user_tweets(username)
            
            for tweet in tweets:
                report = self.process_tweet(tweet, username)
                if report:
                    total_reports += 1
        
        print(f"\n✅ Ingestion complete: {total_reports} new reports")
        return total_reports
    
    def auto_verify_official(self, report: RawReport) -> Optional[Incident]:
        """Auto-verify reports from official sources"""
        source = report.source
        
        # Official sources get instant verification
        if source and source.is_official and source.credibility_score >= 100:
            print(f"🎯 Auto-verifying official source: {source.name}")
            
            # Create incident directly
            from geoalchemy2.elements import WKTElement
            
            location_name = report.location_text or 'Unknown Location'
            location = report.location or WKTElement('POINT(55.27 25.20)', srid=4326)  # Default Dubai
            
            incident = Incident(
                status='CONFIRMED',
                event_type='air_defense',  # Could extract from text
                location_name=location_name,
                location=location,
                description=report.content,
                detected_at=report.posted_at,
                confirmed_at=datetime.utcnow(),
                reports_count=1,
                unique_sources_count=1,
                total_credibility=source.credibility_score,
                verified_by=source.id,
                verification_method='single_official',
                is_active=True
            )
            
            self.db.add(incident)
            self.db.commit()
            self.db.refresh(incident)
            
            # Link report to incident
            report.linked_incident = incident.id
            report.processed = True
            self.db.commit()
            
            print(f"✅ Created CONFIRMED incident: {incident.id}")
            return incident
        
        return None


# Run if executed directly
if __name__ == "__main__":
    import time
    
    print("🚀 Gulf Watch Twitter Ingestion")
    print("=" * 50)
    
    if not TWITTER_BEARER_TOKEN:
        print("\n⚠️ WARNING: TWITTER_BEARER_TOKEN not set")
        print("Set it with: export TWITTER_BEARER_TOKEN='your_token_here'")
        print("\nRunning in demo mode (no actual API calls)")
    
    # Initialize database
    init_database()
    
    # Create ingestion service
    ingestion = TwitterIngestion()
    
    # Run once
    count = ingestion.run_ingestion()
    
    # Auto-verify official sources
    print("\n🔄 Auto-verifying official reports...")
    unprocessed = RawReportCRUD.get_unprocessed(ingestion.db, limit=100)
    verified_count = 0
    
    for report in unprocessed:
        incident = ingestion.auto_verify_official(report)
        if incident:
            verified_count += 1
    
    print(f"\n✅ Verified {verified_count} incidents from official sources")
    print(f"\n📊 Summary:")
    print(f"  - New reports: {count}")
    print(f"  - Auto-verified: {verified_count}")
    
    # Show current incidents
    from models import engine
    from sqlalchemy import text
    
    result = engine.execute(text(
        "SELECT status, event_type, location_name FROM incidents WHERE is_active = true"
    ))
    
    incidents = list(result)
    if incidents:
        print(f"\n📍 Active Incidents ({len(incidents)}):")
        for i in incidents:
            print(f"  - [{i.status}] {i.event_type}: {i.location_name}")
    else:
        print("\n📍 No active incidents")
    
    # Show monitored accounts
    print("\n📡 Monitored Accounts:")
    print("  UAE:", ', '.join(ingestion.UAE_HANDLES))
    print("  Saudi Arabia:", ', '.join(ingestion.SAUDI_HANDLES))
    print("  Qatar:", ', '.join(ingestion.QATAR_HANDLES))
    print("  Bahrain:", ', '.join(ingestion.BAHRAIN_HANDLES))
