import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import re
from collections import defaultdict
import math

@dataclass
class Report:
    """Individual report from any source"""
    id: str
    source_type: str  # 'twitter', 'news', 'telegram', 'user'
    source_id: str    # username, outlet name
    content: str
    created_at: datetime
    location_text: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    media_urls: List[str] = field(default_factory=list)
    raw_data: Dict = field(default_factory=dict)
    
    # Credibility metrics
    follower_count: int = 0
    is_verified: bool = False
    is_media: bool = False
    
    @property
    def credibility_score(self) -> int:
        """Calculate source credibility (0-100)"""
        score = 0
        
        # Base verification
        if self.is_verified:
            score += 50
        
        # Follower count tiers
        if self.follower_count >= 1000000:
            score += 60
        elif self.follower_count >= 100000:
            score += 40
        elif self.follower_count >= 10000:
            score += 20
        
        # Media outlet
        if self.is_media:
            score += 30
        
        # Source type bonuses
        if self.source_type == 'news':
            score += 40
        elif self.source_type == 'telegram_official':
            score += 35
        
        return min(score, 100)

@dataclass  
class Event:
    """Verified/aggregated event"""
    id: str
    status: str  # 'UNCONFIRMED', 'PROBABLE', 'LIKELY', 'CONFIRMED'
    event_type: str
    location_name: str
    location_lat: float
    location_lng: float
    description: str
    first_reported: datetime
    last_updated: datetime
    reports: List[Report] = field(default_factory=list)
    
    @property
    def reports_count(self) -> int:
        return len(self.reports)
    
    @property
    def total_credibility(self) -> int:
        return sum(r.credibility_score for r in self.reports)
    
    @property
    def unique_sources(self) -> int:
        return len(set(r.source_id for r in self.reports))

class KeywordTracker:
    """Track trending keywords from incoming reports"""
    
    KEYWORDS = {
        # Locations
        'dubai', 'abudhabi', 'auh', 'dxb', 'uae', 'bahrain', 'manama', 
        'qatar', 'doha', 'saudi', 'riyadh', 'kuwait', 'oman', 'muscat',
        'palm', 'jumeirah', 'marina', 'downtown', 'burj', 'khalifa',
        'creek', 'harbour', 'deira', 'burdubai', 'jebel', 'ali',
        
        # Threats
        'explosion', 'blast', 'boom', 'explode', 'exploded',
        'missile', 'rocket', 'drone', 'uav', 'attack', 'strike',
        'siren', 'alarm', 'alert', 'raid', 'airraid',
        'smoke', 'fire', 'flame', 'burning',
        'interceptor', 'defense', 'airdefense', 'patriot', 'iron',
        
        # Conflict
        'iran', 'israel', 'war', 'conflict', 'bombing', 'hit', 'struck',
        
        # Arabic
        'انفجار', 'صاروخ', 'طائرة', 'مسيرة', 'إنذار', 'دبي', 'أبوظبي'
    }
    
    def __init__(self):
        self.keyword_counts = defaultdict(int)
        self.last_reset = datetime.now()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract matching keywords from text"""
        text_lower = text.lower()
        found = []
        for keyword in self.KEYWORDS:
            if keyword in text_lower:
                found.append(keyword)
                self.keyword_counts[keyword] += 1
        return found
    
    def get_trending(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top trending keywords"""
        sorted_keywords = sorted(
            self.keyword_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_keywords[:limit]

class LocationExtractor:
    """Extract location mentions from text"""
    
    LOCATION_PATTERNS = {
        'Palm Jumeirah': ['palm', 'palm jumeirah', 'jumeirah', 'fairmont'],
        'Dubai Marina': ['marina', 'dubai marina', 'jbr', 'jumeirah beach'],
        'Downtown Dubai': ['downtown', 'burj khalifa', 'dubai mall', 'business bay'],
        'Dubai Creek Harbour': ['creek', 'creek harbour', 'creek harbor'],
        'Deira': ['deira', 'gold souk', 'naif'],
        'Bur Dubai': ['bur dubai', 'al fahidi', 'karama'],
        'Jebel Ali': ['jebel ali', 'jafza', 'jebel ali port'],
        'Abu Dhabi': ['abu dhabi', 'corniche', 'yas island'],
        'Sharjah': ['sharjah', 'al nahda'],
        'Al Ain': ['al ain'],
        'Fujairah': ['fujairah'],
    }
    
    COORDINATES = {
        'Palm Jumeirah': (25.1156, 55.1284),
        'Dubai Marina': (25.0765, 55.1404),
        'Downtown Dubai': (25.1972, 55.2962),
        'Dubai Creek Harbour': (25.2571, 55.2957),
        'Deira': (25.2708, 55.2962),
        'Bur Dubai': (25.2571, 55.2957),
        'Jebel Ali': (24.9857, 55.0274),
        'Abu Dhabi': (24.4539, 54.3773),
        'Sharjah': (25.3573, 55.4033),
        'Al Ain': (24.1302, 55.8023),
        'Fujairah': (25.1288, 56.3265),
    }
    
    def extract(self, text: str) -> Optional[Tuple[str, float, float]]:
        """Extract location name and coordinates from text"""
        text_lower = text.lower()
        
        for location, patterns in self.LOCATION_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    lat, lng = self.COORDINATES.get(location, (None, None))
                    if lat and lng:
                        return location, lat, lng
        
        return None

class VerificationEngine:
    """Verify events based on multiple reports"""
    
    # Distance threshold for clustering (km)
    CLUSTER_RADIUS_KM = 2.0
    
    # Time window for clustering (minutes)
    TIME_WINDOW_MINUTES = 30
    
    def __init__(self):
        self.pending_reports: List[Report] = []
        self.verified_events: List[Event] = []
        self.location_extractor = LocationExtractor()
    
    def add_report(self, report: Report) -> Optional[Event]:
        """Add report and check if it triggers verification"""
        
        # Extract location if not provided
        if not report.location_lat or not report.location_name:
            location = self.location_extractor.extract(report.content)
            if location:
                report.location_name, report.location_lat, report.location_lng = location
        
        self.pending_reports.append(report)
        
        # Try to cluster and verify
        return self._process_clusters()
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _cluster_reports(self) -> List[List[Report]]:
        """Group reports by location proximity and time"""
        clusters = []
        used = set()
        
        for i, report in enumerate(self.pending_reports):
            if i in used or not report.location_lat:
                continue
            
            cluster = [report]
            used.add(i)
            
            for j, other in enumerate(self.pending_reports):
                if j in used or not other.location_lat:
                    continue
                
                # Check distance
                distance = self._haversine_distance(
                    report.location_lat, report.location_lng,
                    other.location_lat, other.location_lng
                )
                
                # Check time
                time_diff = abs((report.created_at - other.created_at).total_seconds()) / 60
                
                if distance <= self.CLUSTER_RADIUS_KM and time_diff <= self.TIME_WINDOW_MINUTES:
                    cluster.append(other)
                    used.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _determine_event_type(self, reports: List[Report]) -> str:
        """Determine event type from report content"""
        type_keywords = {
            'explosion': ['explosion', 'explode', 'blast', 'boom', 'انفجار'],
            'interceptor': ['interceptor', 'defense', 'patriot', 'air defense', 'launch'],
            'siren': ['siren', 'alarm', 'alert', 'إنذار'],
            'smoke': ['smoke', 'fire', 'burning', 'flame'],
            'drone': ['drone', 'uav', 'مسيرة'],
            'missile': ['missile', 'rocket', 'صاروخ'],
        }
        
        type_counts = defaultdict(int)
        
        for report in reports:
            text_lower = report.content.lower()
            for event_type, keywords in type_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        type_counts[event_type] += 1
        
        if type_counts:
            return max(type_counts, key=type_counts.get)
        return 'unknown'
    
    def _calculate_status(self, reports: List[Report]) -> str:
        """Calculate verification status"""
        unique_sources = len(set(r.source_id for r in reports))
        total_credibility = sum(r.credibility_score for r in reports)
        
        # High credibility source = instant confirmed
        if any(r.credibility_score >= 80 for r in reports):
            return 'CONFIRMED'
        
        # Multiple lower credibility sources
        if unique_sources >= 15 or total_credibility >= 300:
            return 'CONFIRMED'
        elif unique_sources >= 8 or total_credibility >= 150:
            return 'LIKELY'
        elif unique_sources >= 3 or total_credibility >= 50:
            return 'PROBABLE'
        else:
            return 'UNCONFIRMED'
    
    def _process_clusters(self) -> Optional[Event]:
        """Process report clusters and create/update events"""
        clusters = self._cluster_reports()
        
        for cluster in clusters:
            # Skip small clusters
            if len(cluster) < 2:
                continue
            
            # Check if this matches an existing event
            existing_event = self._find_matching_event(cluster)
            
            if existing_event:
                # Update existing event
                existing_event.reports.extend(cluster)
                existing_event.last_updated = datetime.now()
                existing_event.status = self._calculate_status(existing_event.reports)
                return existing_event
            else:
                # Create new event
                event = Event(
                    id=f"evt_{datetime.now().timestamp()}",
                    status=self._calculate_status(cluster),
                    event_type=self._determine_event_type(cluster),
                    location_name=cluster[0].location_name or 'Unknown',
                    location_lat=cluster[0].location_lat or 0,
                    location_lng=cluster[0].location_lng or 0,
                    description=self._generate_description(cluster),
                    first_reported=min(r.created_at for r in cluster),
                    last_updated=datetime.now(),
                    reports=cluster
                )
                self.verified_events.append(event)
                return event
        
        return None
    
    def _find_matching_event(self, cluster: List[Report]) -> Optional[Event]:
        """Find if cluster matches an existing event"""
        for event in self.verified_events:
            for report in cluster:
                if report.location_lat and event.location_lat:
                    distance = self._haversine_distance(
                        report.location_lat, report.location_lng,
                        event.location_lat, event.location_lng
                    )
                    if distance <= self.CLUSTER_RADIUS_KM:
                        return event
        return None
    
    def _generate_description(self, reports: List[Report]) -> str:
        """Generate event description from reports"""
        # Use the most credible report's content
        best_report = max(reports, key=lambda r: r.credibility_score)
        return best_report.content[:200]
    
    def get_events_for_location(
        self, 
        lat: float, 
        lng: float, 
        radius_km: float = 10,
        min_status: str = 'PROBABLE'
    ) -> List[Event]:
        """Get events near a location"""
        status_order = ['UNCONFIRMED', 'PROBABLE', 'LIKELY', 'CONFIRMED']
        min_index = status_order.index(min_status)
        
        nearby = []
        for event in self.verified_events:
            distance = self._haversine_distance(lat, lng, event.location_lat, event.location_lng)
            event_status_index = status_order.index(event.status)
            
            if distance <= radius_km and event_status_index >= min_index:
                nearby.append((event, distance))
        
        # Sort by distance
        nearby.sort(key=lambda x: x[1])
        return [e for e, _ in nearby]

# Demo
if __name__ == "__main__":
    engine = VerificationEngine()
    keyword_tracker = KeywordTracker()
    
    # Simulate incoming reports
    test_reports = [
        Report(
            id="1",
            source_type="twitter",
            source_id="@random_user1",
            content="Loud explosion heard in Palm Jumeirah area!",
            created_at=datetime.now(),
            follower_count=500,
            is_verified=False
        ),
        Report(
            id="2", 
            source_type="twitter",
            source_id="@verified_journalist",
            content="Confirmed: Explosion at Fairmont Hotel, Palm Jumeirah. Emergency services responding.",
            created_at=datetime.now(),
            follower_count=150000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="3",
            source_type="twitter", 
            source_id="@another_user",
            content="Seeing smoke from Palm area. Anyone know what's happening?",
            created_at=datetime.now(),
            follower_count=1200,
            is_verified=False
        ),
    ]
    
    for report in test_reports:
        keywords = keyword_tracker.extract_keywords(report.content)
        print(f"\nReport from {report.source_id}")
        print(f"Keywords: {keywords}")
        print(f"Credibility: {report.credibility_score}")
        
        event = engine.add_report(report)
        if event:
            print(f"\n>>> NEW EVENT: {event.status}")
            print(f"Location: {event.location_name}")
            print(f"Type: {event.event_type}")
            print(f"Sources: {event.unique_sources}")
            print(f"Total credibility: {event.total_credibility}")
    
    print("\n\n=== TRENDING KEYWORDS ===")
    for keyword, count in keyword_tracker.get_trending():
        print(f"{keyword}: {count}")
    
    print("\n\n=== VERIFIED EVENTS ===")
    for event in engine.verified_events:
        print(f"\n[{event.status}] {event.event_type.upper()}")
        print(f"Location: {event.location_name}")
        print(f"Reports: {event.unique_sources} sources, credibility: {event.total_credibility}")
