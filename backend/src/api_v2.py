"""
Gulf Watch API Server v2
Database-backed with real incident storage
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    init_database, get_db, Session as DBSession,
    Incident, Source, RawReport, UserSubscription,
    IncidentCRUD, SourceCRUD, RawReportCRUD, SubscriptionCRUD,
    calculate_distance_km
)
from intelligence.engine import VerificationEngine, Report
from intelligence.official_sources import get_uae_official_sources

app = FastAPI(
    title="Gulf Watch API",
    description="Gulf region threat intelligence platform",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
verification_engine = VerificationEngine()

# ============================================
# Pydantic Schemas
# ============================================

class IncidentResponse(BaseModel):
    id: str
    status: str
    event_type: str
    classification: Optional[str]
    location_name: str
    lat: float
    lng: float
    distance_meters: Optional[float]
    description: Optional[str]
    guidance: Optional[str]
    detected_at: datetime
    reports_count: int
    unique_sources_count: int
    media_urls: List[str]
    
    class Config:
        from_attributes = True

class IncidentDetail(IncidentResponse):
    confirmed_at: Optional[datetime]
    total_credibility: int
    verification_method: Optional[str]

class SourceResponse(BaseModel):
    id: str
    name: str
    handle: str
    platform: str
    source_type: str
    credibility_score: int
    is_official: bool
    country: Optional[str]
    
    class Config:
        from_attributes = True

class RawReportCreate(BaseModel):
    source_handle: str
    source_platform: str = "twitter"
    content: str
    external_id: Optional[str]
    posted_at: datetime
    location_text: Optional[str]
    location_lat: Optional[float]
    location_lng: Optional[float]
    media_urls: List[str] = []
    raw_data: dict = {}

class SubscriptionCreate(BaseModel):
    token: str
    lat: float
    lng: float
    location_name: Optional[str]
    radius_km: int = 50
    notify_confirmed: bool = True
    notify_likely: bool = True
    notify_probable: bool = False
    platform: Optional[str] = "web"

class StatusResponse(BaseModel):
    status: str
    active_incidents: int
    official_sources: int
    database_connected: bool

# ============================================
# API ENDPOINTS
# ============================================

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")


@app.get("/", response_model=StatusResponse)
async def root(db: Session = Depends(get_db)):
    """API status"""
    try:
        active_count = db.query(Incident).filter(
            Incident.is_active == True,
            Incident.status.notin_(['FALSE_ALARM', 'RESOLVED'])
        ).count()
        
        official_count = db.query(Source).filter(
            Source.is_official == True
        ).count()
        
        return StatusResponse(
            status="operational",
            active_incidents=active_count,
            official_sources=official_count,
            database_connected=True
        )
    except Exception as e:
        return StatusResponse(
            status="error",
            active_incidents=0,
            official_sources=0,
            database_connected=False
        )


@app.get("/incidents", response_model=List[IncidentResponse])
async def get_incidents(
    limit: int = Query(50, ge=1, le=200),
    min_status: str = Query("PROBABLE", enum=["UNCONFIRMED", "PROBABLE", "LIKELY", "CONFIRMED"]),
    db: Session = Depends(get_db)
):
    """Get all active incidents"""
    incidents = IncidentCRUD.get_active(db, limit=limit)
    
    # Convert to response format
    response = []
    for i in incidents:
        # Extract lat/lng from geography
        result = db.execute(
            "SELECT ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng FROM incidents WHERE id = :id",
            {'id': i.id}
        ).first()
        
        response.append(IncidentResponse(
            id=str(i.id),
            status=i.status,
            event_type=i.event_type,
            classification=i.classification,
            location_name=i.location_name,
            lat=result.lat if result else 0,
            lng=result.lng if result else 0,
            distance_meters=None,
            description=i.description,
            guidance=i.guidance,
            detected_at=i.detected_at,
            reports_count=i.reports_count,
            unique_sources_count=i.unique_sources_count,
            media_urls=i.media_urls or []
        ))
    
    return response


@app.get("/incidents/nearby", response_model=List[IncidentResponse])
async def get_incidents_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius: float = Query(50.0, ge=1, le=500, description="Radius in km"),
    min_status: str = Query("PROBABLE", enum=["UNCONFIRMED", "PROBABLE", "LIKELY", "CONFIRMED"]),
    db: Session = Depends(get_db)
):
    """Get incidents near a location"""
    results = IncidentCRUD.get_near_location(db, lat, lng, radius, min_status)
    
    return [
        IncidentResponse(
            id=str(r['id']),
            status=r['status'],
            event_type=r['event_type'],
            classification=r.get('classification'),
            location_name=r['location_name'],
            lat=r['lat'],
            lng=r['lng'],
            distance_meters=r['distance_meters'],
            description=r.get('description'),
            guidance=r.get('guidance'),
            detected_at=r['detected_at'],
            reports_count=r.get('reports_count', 0),
            unique_sources_count=r.get('unique_sources_count', 0),
            media_urls=r.get('media_urls') or []
        )
        for r in results
    ]


@app.get("/incidents/{incident_id}", response_model=IncidentDetail)
async def get_incident_detail(
    incident_id: str,
    lat: Optional[float] = Query(None, description="User latitude for distance"),
    lng: Optional[float] = Query(None, description="User longitude for distance"),
    db: Session = Depends(get_db)
):
    """Get detailed incident information"""
    try:
        incident_uuid = UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")
    
    incident = IncidentCRUD.get_by_id(db, incident_uuid)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get coordinates
    result = db.execute(
        "SELECT ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng FROM incidents WHERE id = :id",
        {'id': incident.id}
    ).first()
    
    # Calculate distance if user location provided
    distance = None
    if lat is not None and lng is not None and result:
        distance = calculate_distance_km(lat, lng, result.lat, result.lng) * 1000
    
    return IncidentDetail(
        id=str(incident.id),
        status=incident.status,
        event_type=incident.event_type,
        classification=incident.classification,
        location_name=incident.location_name,
        lat=result.lat if result else 0,
        lng=result.lng if result else 0,
        distance_meters=distance,
        description=incident.description,
        guidance=incident.guidance,
        detected_at=incident.detected_at,
        confirmed_at=incident.confirmed_at,
        reports_count=incident.reports_count,
        unique_sources_count=incident.unique_sources_count,
        total_credibility=incident.total_credibility,
        media_urls=incident.media_urls or [],
        verification_method=incident.verification_method
    )


@app.post("/reports", status_code=201)
async def submit_report(
    report: RawReportCreate,
    db: Session = Depends(get_db)
):
    """Submit a new raw report (for data ingestion)"""
    # Find or create source
    source = SourceCRUD.get_by_handle(db, report.source_handle, report.source_platform)
    
    if not source:
        # Create unknown source with low credibility
        source = Source(
            name=report.source_handle,
            handle=report.source_handle,
            platform=report.source_platform,
            source_type='user',
            credibility_score=10,
            is_verified=False,
            is_official=False
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    
    # Create location geography if provided
    location = None
    if report.location_lat and report.location_lng:
        location = WKTElement(f'POINT({report.location_lng} {report.location_lat})', srid=4326)
    
    # Create raw report
    raw_report = RawReport(
        source_id=source.id,
        external_id=report.external_id,
        content=report.content,
        posted_at=report.posted_at,
        location_text=report.location_text,
        location=location,
        source_credibility=source.credibility_score,
        follower_count=source.follower_count,
        is_verified_source=source.is_verified,
        media_urls=report.media_urls,
        raw_data=report.raw_data,
        processed=False
    )
    
    db.add(raw_report)
    db.commit()
    db.refresh(raw_report)
    
    return {
        "id": str(raw_report.id),
        "status": "received",
        "message": "Report submitted for verification"
    }


@app.get("/sources/official", response_model=List[SourceResponse])
async def get_official_sources(db: Session = Depends(get_db)):
    """Get official (single source of truth) sources"""
    sources = SourceCRUD.get_official_sources(db)
    return [
        SourceResponse(
            id=str(s.id),
            name=s.name,
            handle=s.handle,
            platform=s.platform,
            source_type=s.source_type,
            credibility_score=s.credibility_score,
            is_official=s.is_official,
            country=s.country
        )
        for s in sources
    ]


@app.post("/subscriptions", status_code=201)
async def create_subscription(
    sub: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Create or update a subscription for notifications"""
    subscription = SubscriptionCRUD.create_or_update(
        db,
        token=sub.token,
        lat=sub.lat,
        lng=sub.lng,
        location_name=sub.location_name,
        radius_km=sub.radius_km,
        notify_confirmed=sub.notify_confirmed,
        notify_likely=sub.notify_likely,
        notify_probable=sub.notify_probable,
        platform=sub.platform
    )
    
    return {
        "id": str(subscription.id),
        "token": subscription.subscription_token,
        "status": "active"
    }


@app.delete("/subscriptions/{token}")
async def delete_subscription(
    token: str,
    db: Session = Depends(get_db)
):
    """Deactivate a subscription"""
    sub = db.query(UserSubscription).filter(
        UserSubscription.subscription_token == token
    ).first()
    
    if sub:
        sub.is_active = False
        db.commit()
    
    return {"status": "deleted"}


# ============================================
# ADMIN ENDPOINTS (for operator dashboard)
# ============================================

@app.get("/admin/pending-reports")
async def get_pending_reports(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get unprocessed reports for verification (admin only)"""
    reports = RawReportCRUD.get_unprocessed(db, limit)
    
    return [
        {
            "id": str(r.id),
            "content": r.content[:200],
            "source": r.source.name if r.source else "Unknown",
            "source_type": r.source.source_type if r.source else "unknown",
            "posted_at": r.posted_at,
            "location_text": r.location_text,
            "has_location": r.location is not None
        }
        for r in reports
    ]


@app.post("/admin/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    new_status: str,
    reason: str,
    db: Session = Depends(get_db)
):
    """Manually update incident status (admin only)"""
    try:
        incident_uuid = UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid incident ID")
    
    incident = IncidentCRUD.update_status(
        db, incident_uuid, new_status, reason, method="manual_review"
    )
    
    return {
        "id": str(incident.id),
        "new_status": incident.status,
        "updated_at": incident.updated_at
    }


# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    print("Starting Gulf Watch API v2...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
