"""
Instagram API Integration for Gulf Watch
Monitors official Gulf sources via Instagram
"""
import os
import re
from datetime import datetime
from typing import Optional, List, Dict
import httpx
from sqlalchemy.orm import Session

from models import get_db, RawReport, Source, SourceCRUD

# Instagram credentials (from environment)
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')

class InstagramIngestion:
    """Ingest posts from official Gulf Instagram accounts"""
    
    BASE_URL = "https://graph.instagram.com"
    
    # Official Instagram accounts to monitor (6 countries, no Iran)
    MONITORED_ACCOUNTS = [
        # UAE
        {'username': 'moiuae', 'handle': '@moiuae', 'country': 'UAE', 'name': 'UAE Ministry of Interior'},
        {'username': 'uae_cd', 'handle': '@uae_cd', 'country': 'UAE', 'name': 'UAE Civil Defense'},
        {'username': 'wamnews', 'handle': '@wamnews', 'country': 'UAE', 'name': 'WAM News Agency'},
        {'username': 'dubaipolicehq', 'handle': '@dubaipolicehq', 'country': 'UAE', 'name': 'Dubai Police'},
        # Saudi
        {'username': 'saudimoi', 'handle': '@saudimoi', 'country': 'Saudi Arabia', 'name': 'Saudi Ministry of Interior'},
        {'username': 'saudi_cd', 'handle': '@saudi_cd', 'country': 'Saudi Arabia', 'name': 'Saudi Civil Defense'},
        # Qatar
        {'username': 'moi_qatar', 'handle': '@moi_qatar', 'country': 'Qatar', 'name': 'Qatar Ministry of Interior'},
        {'username': 'qna.qa', 'handle': '@qna.qa', 'country': 'Qatar', 'name': 'Qatar News Agency'},
        # Bahrain
        {'username': 'moi_bahrain', 'handle': '@moi_bahrain', 'country': 'Bahrain', 'name': 'Bahrain Ministry of Interior'},
        # Kuwait
        {'username': 'moikuwait', 'handle': '@moikuwait', 'country': 'Kuwait', 'name': 'Kuwait Ministry of Interior'},
        {'username': 'kuwait_cd', 'handle': '@kuwait_cd', 'country': 'Kuwait', 'name': 'Kuwait Civil Defense'},
        # Israel
        {'username': 'idf', 'handle': '@idf', 'country': 'Israel', 'name': 'Israel Defense Forces'},
        {'username': 'israelpolice', 'handle': '@israelpolice', 'country': 'Israel', 'name': 'Israel Police'},
    ]
    
    # Keywords that indicate threats/incidents
    THREAT_KEYWORDS = [
        'explosion', 'blast', 'attack', 'missile', 'drone', 'uav',
        'air defense', 'interceptor', 'siren', 'alert', 'emergency',
        'strike', 'impact', 'exploded', 'smoke', 'fire', 'warning',
        'انفجار', 'صاروخ', 'طائرة', 'مسيرة', 'إنذار', 'تحذير'
    ]
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.headers = {
            "Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"
        } if INSTAGRAM_ACCESS_TOKEN else {}
    
    def is_threat_related(self, text: str) -> bool:
        """Check if post is threat-related"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.THREAT_KEYWORDS)
    
    def process_post(self, post: Dict, account: Dict) -> Optional[RawReport]:
        """Process an Instagram post into a raw report"""
        text = post.get('caption', '')
        post_id = post.get('id')
        created_at = post.get('timestamp')
        
        # Skip if not threat-related
        if not self.is_threat_related(text):
            return None
        
        # Check if already processed
        existing = self.db.query(RawReport).filter(
            RawReport.external_id == post_id
        ).first()
        
        if existing:
            return None
        
        # Get or create source
        handle = account['handle']
        source = SourceCRUD.get_by_handle(self.db, handle, "instagram")
        
        if not source:
            # Create source
            source = Source(
                name=account['name'],
                handle=handle,
                platform="instagram",
                source_type="government",
                credibility_score=90,
                is_official=True,
                country=account['country']
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
            print(f"✅ Created Instagram source: {handle}")
        
        # Parse timestamp
        try:
            posted_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            posted_at = datetime.utcnow()
        
        # Create raw report
        raw_report = RawReport(
            source_id=source.id,
            external_id=post_id,
            content=text,
            posted_at=posted_at,
            source_credibility=source.credibility_score,
            is_verified_source=source.is_verified,
            raw_data=post,
            processed=False
        )
        
        self.db.add(raw_report)
        self.db.commit()
        self.db.refresh(raw_report)
        
        print(f"✅ Created Instagram report from {handle}: {text[:50]}...")
        return raw_report
    
    def run_ingestion(self) -> int:
        """Run full Instagram ingestion cycle"""
        if not INSTAGRAM_ACCESS_TOKEN:
            print("⚠️ No Instagram API token set")
            return 0
        
        total_new = 0
        
        for account in self.MONITORED_ACCOUNTS:
            try:
                print(f"🔍 Checking Instagram: {account['handle']}")
                # Note: Actual Instagram API integration would require
                # business account setup and proper API calls
                # This is a placeholder for the structure
                pass
            except Exception as e:
                print(f"❌ Error processing {account['handle']}: {e}")
        
        return total_new
