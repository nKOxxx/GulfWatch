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
    """Load demo reports for testing"""
    demo_reports = [
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
        Report(
            id="r4",
            source_type="twitter",
            source_id="dubai_eye",
            content="Air defense interceptors launched over Palm area. Multiple booms heard.",
            created_at=datetime.now(),
            location_name="Palm Jumeirah",
            location_lat=25.1156,
            location_lng=55.1284,
            follower_count=450000,
            is_verified=True,
            is_media=True
        ),
        Report(
            id="r5",
            source_type="user",
            source_id="anonymous",
            content="Sirens going off in Downtown. Everyone heading to parking shelters.",
            created_at=datetime.now(),
            location_name="Downtown Dubai",
            location_lat=25.1972,
            location_lng=55.2962,
            follower_count=0,
            is_verified=False
        ),
        Report(
            id="r6",
            source_type="twitter",
            source_id="witness_marina",
            content="Debris falling near Marina Walk. Stay clear of the area.",
            created_at=datetime.now(),
            location_name="Dubai Marina",
            location_lat=25.0765,
            location_lng=55.1404,
            follower_count=800,
            is_verified=False
        ),
        Report(
            id="r7",
            source_type="twitter",
            source_id="gulf_news",
            content="Jebel Ali Port reports fire at one of the berths. Fire crews on scene.",
            created_at=datetime.now(),
            location_name="Jebel Ali",
            location_lat=24.9857,
            location_lng=55.0274,
            follower_count=1800000,
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
