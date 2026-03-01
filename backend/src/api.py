"""
Gulf Watch API Server
Minimal API serving verified events
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add intelligence module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intelligence.engine import VerificationEngine, Report
from intelligence.ingestion import IngestionService

app = FastAPI(title="Gulf Watch API", version="0.1.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
service = IngestionService()

# Load demo data for testing
def load_demo_data():
    """Load demo reports for testing across all regions"""
    demo_reports = [
        # UAE - Dubai
        Report(
            id="r1",
            source_type="twitter",
            source_id="CivilDefenseUAE",
            content="Interceptor systems activated. Stay indoors, away from windows. Follow official channels only.",
            created_at=datetime.now(),
            location_name="Dubai",
            location_lat=25.2048,
            location_lng=55.2708,
            follower_count=500000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="r2",
            source_type="twitter",
            source_id="reuters",
            content="Explosion at Fairmont Hotel, Palm Jumeirah. Emergency services responding to multiple casualties.",
            created_at=datetime.now(),
            location_name="Palm Jumeirah",
            location_lat=25.1156,
            location_lng=55.1284,
            follower_count=25000000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="r3",
            source_type="twitter",
            source_id="ahmed_dxb",
            content="Loud explosion from Creek Harbour direction. Saw smoke rising near the water.",
            created_at=datetime.now(),
            location_name="Dubai Creek Harbour",
            location_lat=25.2571,
            location_lng=55.2957,
            follower_count=1200,
            is_verified=False
        ),
        # UAE - Abu Dhabi
        Report(
            id="r8",
            source_type="twitter",
            source_id="WAMews",
            content="Air defense systems intercept hostile targets over Abu Dhabi. All residents advised to remain indoors.",
            created_at=datetime.now(),
            location_name="Abu Dhabi",
            location_lat=24.4539,
            location_lng=54.3773,
            follower_count=2000000,
            is_verified=True,
            is_media=True
        ),
        # Bahrain
        Report(
            id="r9",
            source_type="twitter",
            source_id="bahrain_news",
            content="Explosion heard in Manama. Cause under investigation. Emergency services responding.",
            created_at=datetime.now(),
            location_name="Manama",
            location_lat=26.2285,
            location_lng=50.5860,
            follower_count=500000,
            is_verified=True,
            is_media=True
        ),
        # Qatar
        Report(
            id="r10",
            source_type="twitter",
            source_id="doha_observer",
            content="Air raid sirens tested in Doha. This is a drill. No cause for concern.",
            created_at=datetime.now(),
            location_name="Doha",
            location_lat=25.2854,
            location_lng=51.5310,
            follower_count=300000,
            is_verified=True,
            is_media=True
        ),
        # Saudi Arabia
        Report(
            id="r11",
            source_type="twitter",
            source_id="saudi_news",
            content="Missile intercepted over Riyadh. Debris fell in uninhabited area. No casualties reported.",
            created_at=datetime.now(),
            location_name="Riyadh",
            location_lat=24.7136,
            location_lng=46.6753,
            follower_count=5000000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="r12",
            source_type="twitter",
            source_id="jeddah_eye",
            content="Loud explosion heard near Jeddah port. Authorities investigating.",
            created_at=datetime.now(),
            location_name="Jeddah",
            location_lat=21.4858,
            location_lng=39.1925,
            follower_count=150000,
            is_verified=False,
            is_media=True
        ),
        # Israel
        Report(
            id="r13",
            source_type="twitter",
            source_id="idf",
            content="Iron Dome intercepts multiple rockets over Tel Aviv area. Stay near shelters.",
            created_at=datetime.now(),
            location_name="Tel Aviv",
            location_lat=32.0853,
            location_lng=34.7818,
            follower_count=2000000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="r14",
            source_type="twitter",
            source_id="jerusalem_post",
            content="Sirens in Jerusalem. Explosions heard. Iron Dome active.",
            created_at=datetime.now(),
            location_name="Jerusalem",
            location_lat=31.7683,
            location_lng=35.2137,
            follower_count=800000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="r15",
            source_type="twitter",
            source_id="haifa_alerts",
            content="Multiple interceptor launches visible from Haifa. Loud booms reported.",
            created_at=datetime.now(),
            location_name="Haifa",
            location_lat=32.7940,
            location_lng=34.9896,
            follower_count=200000,
            is_verified=True,
            is_media=True
        ),
        # Iran
        Report(
            id="r16",
            source_type="twitter",
            source_id="tehran_journal",
            content="Explosions reported in Tehran. Location unknown at this time.",
            created_at=datetime.now(),
            location_name="Tehran",
            location_lat=35.6892,
            location_lng=51.3890,
            follower_count=400000,
            is_verified=False,
            is_media=True
        ),
        Report(
            id="r17",
            source_type="twitter",
            source_id="isfahan_news",
            content="Military facility near Isfahan. All normal operations.",
            created_at=datetime.now(),
            location_name="Isfahan",
            location_lat=32.6539,
            location_lng=51.6660,
            follower_count=100000,
            is_verified=True,
            is_media=True
        ),
        # Lebanon
        Report(
            id="r18",
            source_type="twitter",
            source_id="beirut_reports",
            content="Explosion in Beirut southern suburbs. Ambulances responding.",
            created_at=datetime.now(),
            location_name="Beirut",
            location_lat=33.8938,
            location_lng=35.5018,
            follower_count=600000,
            is_verified=False,
            is_media=True
        ),
        # Jordan
        Report(
            id="r19",
            source_type="twitter",
            source_id="amman_alerts",
            content="Air defense activity near Aqaba. Debris from interceptions may fall in area.",
            created_at=datetime.now(),
            location_name="Aqaba",
            location_lat=29.5267,
            location_lng=35.0078,
            follower_count=150000,
            is_verified=True,
            is_media=True
        ),
        # Kuwait
        Report(
            id="r20",
            source_type="twitter",
            source_id="kuwait_moi",
            content="No threats to Kuwait airspace. All systems normal.",
            created_at=datetime.now(),
            location_name="Kuwait City",
            location_lat=29.3759,
            location_lng=47.9774,
            follower_count=800000,
            is_verified=True,
            is_media=True
        ),
        # Oman
        Report(
            id="r21",
            source_type="twitter",
            source_id="muscat_daily",
            content="Flight diversions due to regional airspace closure. Muscat airport operating normally.",
            created_at=datetime.now(),
            location_name="Muscat",
            location_lat=23.5859,
            location_lng=58.4059,
            follower_count=200000,
            is_verified=True,
            is_media=True
        ),
    ]
    
    for report in demo_reports:
        service.keyword_tracker.extract_keywords(report.content)
        service.engine.add_report(report)

# Load demo data on startup
load_demo_data()

# Pydantic models
class EventResponse(BaseModel):
    id: str
    status: str
    event_type: str
    location_name: str
    location_lat: float
    location_lng: float
    description: str
    first_reported: datetime
    reports_count: int
    total_credibility: int
    unique_sources: int

class ReportRequest(BaseModel):
    content: str
    location: str
    event_type: Optional[str] = None

class TrendingResponse(BaseModel):
    keyword: str
    count: int

# Routes
@app.get("/")
def root():
    return {
        "service": "Gulf Watch API",
        "version": "0.1.0",
        "status": "operational",
        "events": len(service.engine.verified_events),
        "timestamp": datetime.now()
    }

@app.get("/events", response_model=List[EventResponse])
def get_events(
    lat: Optional[float] = Query(None, description="User latitude"),
    lng: Optional[float] = Query(None, description="User longitude"),
    radius: float = Query(20, description="Search radius in km"),
    min_status: str = Query("PROBABLE", description="Minimum verification status")
):
    """Get verified events near a location"""
    
    # If no location provided, return all events
    if lat is None or lng is None:
        events = service.engine.verified_events
    else:
        events = service.get_events(lat, lng, radius)
    
    # Filter by status
    status_order = ['UNCONFIRMED', 'PROBABLE', 'LIKELY', 'CONFIRMED']
    min_index = status_order.index(min_status) if min_status in status_order else 0
    
    filtered = [e for e in events if status_order.index(e.status) >= min_index]
    
    return [
        EventResponse(
            id=e.id,
            status=e.status,
            event_type=e.event_type,
            location_name=e.location_name,
            location_lat=e.location_lat,
            location_lng=e.location_lng,
            description=e.description,
            first_reported=e.first_reported,
            reports_count=e.reports_count,
            total_credibility=e.total_credibility,
            unique_sources=e.unique_sources
        )
        for e in filtered
    ]

@app.get("/events/nearby")
def get_nearby_events(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius: float = Query(10, description="Search radius in km")
):
    """Get events specifically for nearby display"""
    events = service.get_events(lat, lng, radius)
    
    # Categorize
    critical = []
    warning = []
    info = []
    
    for e in events:
        if e.status == 'CONFIRMED' and e.event_type in ['explosion', 'missile']:
            critical.append(e)
        elif e.status in ['CONFIRMED', 'LIKELY']:
            warning.append(e)
        else:
            info.append(e)
    
    return {
        "critical": len(critical),
        "warning": len(warning),
        "info": len(info),
        "events": [
            {
                "id": e.id,
                "status": e.status,
                "type": e.event_type,
                "location": e.location_name,
                "distance_km": calculate_distance(lat, lng, e.location_lat, e.location_lng),
                "description": e.description[:100],
                "sources": e.unique_sources,
                "verified": e.status in ['CONFIRMED', 'LIKELY']
            }
            for e in events[:10]  # Limit to 10
        ]
    }

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance in km"""
    import math
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = (math.sin(delta_lat/2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)

@app.get("/trending", response_model=List[TrendingResponse])
def get_trending(limit: int = 10):
    """Get trending keywords"""
    trending = service.get_trending(limit)
    return [TrendingResponse(keyword=k, count=c) for k, c in trending]

@app.post("/report")
def submit_report(report: ReportRequest):
    """Submit a new user report"""
    
    # Create report
    new_report = Report(
        id=f"user_{datetime.now().timestamp()}",
        source_type="user",
        source_id="anonymous",
        content=report.content,
        created_at=datetime.now(),
        location_name=report.location,
        follower_count=0,
        is_verified=False
    )
    
    # Extract keywords
    service.keyword_tracker.extract_keywords(new_report.content)
    
    # Add to engine
    event = service.engine.add_report(new_report)
    
    return {
        "success": True,
        "report_id": new_report.id,
        "event_created": event is not None,
        "event_status": event.status if event else None
    }

@app.get("/stats")
def get_stats():
    """Get system stats"""
    events = service.engine.verified_events
    
    return {
        "total_events": len(events),
        "confirmed": len([e for e in events if e.status == 'CONFIRMED']),
        "likely": len([e for e in events if e.status == 'LIKELY']),
        "probable": len([e for e in events if e.status == 'PROBABLE']),
        "unconfirmed": len([e for e in events if e.status == 'UNCONFIRMED']),
        "pending_reports": len(service.engine.pending_reports),
        "trending_keywords": len(service.keyword_tracker.keyword_counts)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)
