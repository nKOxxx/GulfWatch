import asyncio
import aiohttp
import json
from datetime import datetime
from typing import AsyncGenerator, List, Dict
import os

from engine import Report, VerificationEngine, KeywordTracker

class TwitterIngester:
    """Ingest Twitter/X data for Gulf Watch"""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
    
    async def search_recent(
        self, 
        query: str,
        max_results: int = 100
    ) -> List[Dict]:
        """Search recent tweets"""
        url = f"{self.base_url}/tweets/search/recent"
        
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,author_id,geo,public_metrics",
            "user.fields": "verified,public_metrics,description",
            "expansions": "author_id"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_tweets(data)
                else:
                    print(f"Twitter API error: {resp.status}")
                    return []
    
    def _parse_tweets(self, data: Dict) -> List[Report]:
        """Parse Twitter API response into Reports"""
        reports = []
        
        tweets = data.get("data", [])
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
        
        for tweet in tweets:
            author_id = tweet.get("author_id")
            user = users.get(author_id, {})
            
            # Extract metrics
            metrics = tweet.get("public_metrics", {})
            user_metrics = user.get("public_metrics", {})
            
            # Check if media/journalist
            bio = user.get("description", "").lower()
            is_media = any(word in bio for word in ["journalist", "reporter", "news", "editor"])
            
            report = Report(
                id=tweet["id"],
                source_type="twitter",
                source_id=user.get("username", "unknown"),
                content=tweet["text"],
                created_at=datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")),
                raw_data=tweet,
                follower_count=user_metrics.get("followers_count", 0),
                is_verified=user.get("verified", False),
                is_media=is_media
            )
            
            # Try to extract geo
            geo = tweet.get("geo")
            if geo and "coordinates" in geo:
                coords = geo["coordinates"]["coordinates"]
                report.location_lng = coords[0]
                report.location_lat = coords[1]
            
            reports.append(report)
        
        return reports
    
    async def stream_filtered(
        self,
        keywords: List[str],
        engine: VerificationEngine,
        keyword_tracker: KeywordTracker,
        poll_interval: int = 30
    ):
        """Continuously poll for new tweets matching keywords"""
        
        query = " OR ".join(keywords) + " -is:retweet"
        
        print(f"Starting Twitter stream for: {keywords}")
        
        while True:
            try:
                reports = await self.search_recent(query, max_results=50)
                
                for report in reports:
                    # Track keywords
                    keywords_found = keyword_tracker.extract_keywords(report.content)
                    
                    # Add to verification engine
                    event = engine.add_report(report)
                    
                    if event and event.status in ['LIKELY', 'CONFIRMED']:
                        print(f"\n🔔 NEW {event.status} EVENT")
                        print(f"  Type: {event.event_type}")
                        print(f"  Location: {event.location_name}")
                        print(f"  Sources: {event.unique_sources}")
                        print(f"  Credibility: {event.total_credibility}")
                
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                print(f"Stream error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

class NewsIngester:
    """Ingest from news APIs and RSS feeds"""
    
    # High-credibility sources
    TRUSTED_SOURCES = {
        'reuters.com': 90,
        'apnews.com': 90,
        'bbc.com': 85,
        'aljazeera.com': 85,
        'gulfnews.com': 80,
        'khaleejtimes.com': 80,
        'thenationalnews.com': 80,
        'wam.ae': 95,  # UAE official
        'bna.bh': 95,  # Bahrain official
    }
    
    async def fetch_rss(self, feed_url: str) -> List[Report]:
        """Fetch and parse RSS feed"""
        # Would use feedparser in production
        pass
    
    def parse_news_article(self, title: str, content: str, source: str, url: str) -> Report:
        """Parse news article into Report"""
        
        # Determine credibility from source
        credibility = 0
        for domain, score in self.TRUSTED_SOURCES.items():
            if domain in source or domain in url:
                credibility = score
                break
        
        return Report(
            id=f"news_{hash(url)}",
            source_type="news",
            source_id=source,
            content=f"{title}. {content}",
            created_at=datetime.now(),
            raw_data={"url": url},
            is_media=True,
            follower_count=1000000 if credibility >= 80 else 100000
        )

class TelegramIngester:
    """Ingest from Telegram channels"""
    
    # Official UAE channels
    OFFICIAL_CHANNELS = [
        'dubaicivildefence',
        'uae_gov',
        'moiuae',
    ]
    
    async def fetch_channel(self, channel: str, bot_token: str) -> List[Report]:
        """Fetch recent messages from Telegram channel"""
        # Would use python-telegram-bot in production
        pass

# Main ingestion service
class IngestionService:
    """Main service coordinating all ingestions"""
    
    KEYWORDS = [
        'dubai', 'abudhabi', 'uae', 'bahrain', 'qatar', 'doha',
        'explosion', 'blast', 'attack', 'missile', 'drone', 'strike',
        'siren', 'alert', 'interceptor', 'air defense',
        'palm', 'jumeirah', 'marina', 'downtown', 'burj khalifa',
        'iran', 'israel', 'war'
    ]
    
    def __init__(self):
        self.engine = VerificationEngine()
        self.keyword_tracker = KeywordTracker()
        self.twitter = None
        
        # Initialize Twitter if token available
        twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
        if twitter_token:
            self.twitter = TwitterIngester(twitter_token)
    
    async def run(self):
        """Run all ingestion streams"""
        tasks = []
        
        if self.twitter:
            tasks.append(
                self.twitter.stream_filtered(
                    self.KEYWORDS,
                    self.engine,
                    self.keyword_tracker,
                    poll_interval=30
                )
            )
        
        # Add other ingestions here
        
        if tasks:
            await asyncio.gather(*tasks)
        else:
            print("No ingestion sources configured. Set TWITTER_BEARER_TOKEN")
    
    def get_events(self, lat: float, lng: float, radius: float = 10):
        """Get verified events near location"""
        return self.engine.get_events_for_location(lat, lng, radius)
    
    def get_trending(self, limit: int = 10):
        """Get trending keywords"""
        return self.keyword_tracker.get_trending(limit)

if __name__ == "__main__":
    service = IngestionService()
    
    # Demo mode - simulate without API
    print("Gulf Watch Intelligence Service")
    print("================================\n")
    
    if not os.getenv('TWITTER_BEARER_TOKEN'):
        print("⚠️  TWITTER_BEARER_TOKEN not set")
        print("Running demo mode with simulated data...\n")
        
        # Simulate some reports
        from engine import Report
        
        demo_reports = [
            Report(id="1", source_type="twitter", source_id="@user1",
                   content="Explosion heard in Palm Jumeirah!", 
                   created_at=datetime.now(), follower_count=500),
            Report(id="2", source_type="twitter", source_id="@reporter_dxb",
                   content="Confirmed: Fairmont Hotel Palm Jumeirah hit. Emergency responding.",
                   created_at=datetime.now(), follower_count=150000, is_verified=True, is_media=True),
            Report(id="3", source_type="twitter", source_id="@resident2",
                   content="Palm area - loud boom and smoke visible",
                   created_at=datetime.now(), follower_count=1200),
            Report(id="4", source_type="twitter", source_id="@journalist",
                   content="Air defense interceptors launched over Dubai. Multiple targets engaged.",
                   created_at=datetime.now(), follower_count=50000, is_verified=True, is_media=True),
            Report(id="5", source_type="twitter", source_id="@witness",
                   content="Seeing smoke from Marina area now",
                   created_at=datetime.now(), follower_count=800),
        ]
        
        for report in demo_reports:
            service.keyword_tracker.extract_keywords(report.content)
            event = service.engine.add_report(report)
            
            if event:
                print(f"\n🚨 {event.status}: {event.event_type.upper()}")
                print(f"   📍 {event.location_name}")
                print(f"   👥 {event.unique_sources} sources (credibility: {event.total_credibility})")
                print(f"   📝 {event.description[:80]}...")
        
        print("\n\n📊 TRENDING KEYWORDS:")
        for kw, count in service.get_trending(5):
            print(f"   {kw}: {count}")
        
        print("\n\n📍 EVENTS NEAR CREEK HARBOUR:")
        events = service.get_events(25.2571, 55.2957, radius_km=15)
        for e in events:
            print(f"   [{e.status}] {e.event_type} at {e.location_name}")
    else:
        # Run real ingestion
        asyncio.run(service.run())
