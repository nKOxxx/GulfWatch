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
from sqlalchemy import text
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
    country: Optional[str]
    lat: float
    lng: float
    distance_meters: Optional[float]
    description: Optional[str]
    guidance: Optional[str]
    detected_at: datetime
    reports_count: int
    unique_sources_count: int
    media_urls: List[str]
    # Source info
    source_name: Optional[str]
    source_handle: Optional[str]
    source_platform: Optional[str]
    source_url: Optional[str]
    
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


@app.get("/admin/init-db")
@app.post("/admin/init-db")
async def initialize_database():
    """Initialize database - enable PostGIS and create tables"""
    from sqlalchemy import text
    from models import engine
    
    try:
        with engine.connect() as conn:
            # Enable PostGIS
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            conn.commit()
            
            # Verify
            result = conn.execute(text("SELECT PostGIS_Version();"))
            version = result.scalar()
            
        # Create tables
        init_database()
        
        return {
            "status": "success",
            "message": "Database initialized",
            "postgis_version": version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")


@app.get("/admin/ingest-twitter")
@app.post("/admin/ingest-twitter")
async def ingest_twitter(db: Session = Depends(get_db)):
    """Manually trigger Twitter ingestion (admin only)"""
    try:
        from ingestion.twitter import TwitterIngestion
        
        ingestion = TwitterIngestion(db)
        new_reports = ingestion.run_ingestion()
        
        # Auto-verify official sources
        from models import RawReportCRUD
        unprocessed = RawReportCRUD.get_unprocessed(db, limit=100)
        verified_count = 0
        
        for report in unprocessed:
            incident = ingestion.auto_verify_official(report)
            if incident:
                verified_count += 1
        
        return {
            "status": "success",
            "new_reports": new_reports,
            "auto_verified": verified_count,
            "message": f"Ingested {new_reports} reports, auto-verified {verified_count} incidents"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/admin/demo-incidents")
async def create_demo_incidents(db: Session = Depends(get_db)):
    """Create demo incidents for testing (admin only)"""
    try:
        from geoalchemy2.elements import WKTElement
        from datetime import datetime
        from models import Incident, Source
        
        # Get official source
        source = db.query(Source).filter(Source.handle == "uae_cd").first()
        source_id = source.id if source else None
        
        # Create demo incidents
        demos = [
            {
                "status": "CONFIRMED",
                "event_type": "Air Defense",
                "location_name": "Dubai Marina",
                "location": WKTElement('POINT(55.1404 25.0765)', srid=4326),
                "description": "Air defense systems activated over Dubai. Interception confirmed.",
                "guidance": "Stay indoors. Away from windows. Follow official channels only.",
                "verified_by": source_id,
                "verification_method": "single_official"
            },
            {
                "status": "PROBABLE",
                "event_type": "Explosion",
                "location_name": "Abu Dhabi",
                "location": WKTElement('POINT(54.3773 24.4539)', srid=4326),
                "description": "Reports of explosion heard in multiple locations. Awaiting confirmation."
            }
        ]
        
        created = []
        for demo in demos:
            incident = Incident(
                **demo,
                detected_at=datetime.utcnow(),
                confirmed_at=datetime.utcnow() if demo.get("verified_by") else None,
                is_active=True,
                reports_count=1,
                unique_sources_count=1,
                total_credibility=100 if demo.get("verified_by") else 30
            )
            db.add(incident)
            created.append(incident)
        
        db.commit()
        
        return {
            "status": "success",
            "created": len(created),
            "incidents": [{"id": str(i.id), "type": i.event_type, "location": i.location_name} for i in created]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo creation failed: {str(e)}")


@app.post("/admin/convert-reports")
async def convert_pending_reports(db: Session = Depends(get_db)):
    """Convert all pending reports to verified incidents (admin only)"""
    try:
        from geoalchemy2.elements import WKTElement
        from models import RawReport, Source
        
        # Get all unprocessed reports
        unprocessed = db.query(RawReport).filter(RawReport.processed == False).all()
        
        created_incidents = []
        
        # Map handles to countries
        handle_to_country = {
            'mofaqatar_en': 'Qatar',
            'moi_qataren': 'Qatar',
            'qnaenglish': 'Qatar',
            'saudimoi': 'Saudi Arabia',
            'saudidcd': 'Saudi Arabia',
            'sparegions': 'Saudi Arabia',
            'bahrainnews': 'Bahrain',
            'moi_bahrain': 'Bahrain',
            'uae_cd': 'UAE',
            'wamnews': 'UAE',
            'dubaipolicehq': 'UAE',
            'adpolicehq': 'UAE',
            'moiuae': 'UAE',
            'moikuwait': 'Kuwait',
            'kuw_civil_def': 'Kuwait',
            'kuna_en': 'Kuwait',
            'idf': 'Israel',
            'idfhomefront': 'Israel',
            'ilpolice': 'Israel',
            'israelipm': 'Israel',
            'irimfa_en': 'Iran',
            'irgcofficial': 'Iran',
            'tasnimnews_en': 'Iran',
            'presstv': 'Iran'
        }
        
        for report in unprocessed:
            # Determine country from source handle
            handle_lower = report.source.handle.lower() if report.source else ''
            country = handle_to_country.get(handle_lower, 'Unknown')
            
            # Determine status based on content
            content_lower = report.content.lower()
            if any(word in content_lower for word in ['confirmed', 'intercepted', 'all clear', 'completed']):
                status = 'CONFIRMED'
            elif any(word in content_lower for word in ['likely', 'probable', 'monitoring']):
                status = 'LIKELY'
            else:
                status = 'PROBABLE'
            
            # Build source URL
            source_url = None
            if report.external_id and report.source_platform == 'twitter':
                source_url = f"https://x.com/{report.source.handle}/status/{report.external_id}"
            
            # Create incident
            incident = Incident(
                status=status,
                event_type='security_alert',
                location_name=report.location_text or 'Unknown Location',
                country=country,
                location=WKTElement(f'POINT({report.location.lng} {report.location.lat})', srid=4326) if report.location else None,
                description=report.content[:500],
                guidance='Follow official instructions. Monitor local media.',
                detected_at=report.posted_at or datetime.utcnow(),
                reports_count=1,
                unique_sources_count=1,
                total_credibility=report.source_credibility or 50,
                is_active=False,  # Historical
                media_urls=report.media_urls or [],
                # Source info
                source_handle=report.source.handle if report.source else None,
                source_name=report.source.name if report.source else None,
                source_platform=report.source_platform,
                external_id=report.external_id,
                source_url=source_url
            )
            
            db.add(incident)
            report.processed = True
            created_incidents.append(incident)
        
        db.commit()
        
        return {
            "status": "success",
            "converted": len(created_incidents),
            "incidents": [{"id": str(i.id), "location": i.location_name, "country": i.country} for i in created_incidents]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@app.get("/admin/historical-data")
@app.post("/admin/historical-data")
async def create_historical_data(db: Session = Depends(get_db)):
    """
    Create 72 hours of realistic historical incident data.
    Includes incidents from UAE, Saudi Arabia, Qatar, and Bahrain.
    """
    try:
        from geoalchemy2.elements import WKTElement
        from datetime import datetime, timedelta
        from models import Incident
        
        now = datetime.utcnow()
        
        # Historical incidents - 72 hours of realistic data
        historical_incidents = [
            # 72 hours ago - Dubai air defense
            {
                "status": "CONFIRMED",
                "event_type": "air_defense",
                "location_name": "Downtown Dubai",
                "location": WKTElement('POINT(55.2962 25.1972)', srid=4326),
                "description": "Air defense systems activated over Downtown Dubai. Interception of hostile drone confirmed by Civil Defense.",
                "guidance": "Remain indoors. Avoid windows. Follow official instructions.",
                "detected_at": now - timedelta(hours=72),
                "confirmed_at": now - timedelta(hours=71, minutes=45),
                "reports_count": 12,
                "unique_sources_count": 5,
                "total_credibility": 280,
                "verification_method": "multiple_official",
                "is_active": False,
                "region": "Dubai",
                "country": "UAE"
            },
            # 70 hours ago - Siren test Dubai
            {
                "status": "CONFIRMED",
                "event_type": "siren",
                "location_name": "Dubai Marina",
                "location": WKTElement('POINT(55.1404 25.0765)', srid=4326),
                "description": "Emergency siren activation drill conducted across Dubai Marina area. This was a planned test.",
                "guidance": "This was a drill. No action required.",
                "detected_at": now - timedelta(hours=70),
                "confirmed_at": now - timedelta(hours=70),
                "reports_count": 3,
                "unique_sources_count": 2,
                "total_credibility": 150,
                "verification_method": "official_announcement",
                "is_active": False,
                "region": "Dubai",
                "country": "UAE"
            },
            # 66 hours ago - Explosion report (false alarm)
            {
                "status": "FALSE_ALARM",
                "event_type": "explosion",
                "location_name": "Jebel Ali",
                "location": WKTElement('POINT(55.0274 24.9857)', srid=4326),
                "description": "Reports of explosion near Jebel Ali port area investigated. Determined to be construction demolition. No threat.",
                "guidance": "False alarm. No action required.",
                "detected_at": now - timedelta(hours=66),
                "confirmed_at": now - timedelta(hours=65),
                "reports_count": 8,
                "unique_sources_count": 3,
                "total_credibility": 90,
                "verification_method": "official_investigation",
                "is_active": False,
                "region": "Dubai",
                "country": "UAE"
            },
            # 60 hours ago - Abu Dhabi drone alert
            {
                "status": "LIKELY",
                "event_type": "drone",
                "location_name": "Abu Dhabi",
                "location": WKTElement('POINT(54.3773 24.4539)', srid=4326),
                "description": "Multiple reports of drone activity near Abu Dhabi industrial zone. Authorities monitoring situation.",
                "guidance": "Stay vigilant. Report suspicious activity.",
                "detected_at": now - timedelta(hours=60),
                "confirmed_at": None,
                "reports_count": 6,
                "unique_sources_count": 4,
                "total_credibility": 120,
                "verification_method": "corroboration",
                "is_active": False,
                "region": "Abu Dhabi",
                "country": "UAE"
            },
            # 54 hours ago - Sharjah alert
            {
                "status": "PROBABLE",
                "event_type": "siren",
                "location_name": "Sharjah",
                "location": WKTElement('POINT(55.4033 25.3573)', srid=4326),
                "description": "Emergency alert sirens activated in Sharjah. Reason unclear, authorities investigating.",
                "guidance": "Monitor official channels for updates.",
                "detected_at": now - timedelta(hours=54),
                "confirmed_at": None,
                "reports_count": 4,
                "unique_sources_count": 2,
                "total_credibility": 60,
                "verification_method": "single_source",
                "is_active": False,
                "region": "Sharjah",
                "country": "UAE"
            },
            # 48 hours ago - Saudi interceptor activation
            {
                "status": "CONFIRMED",
                "event_type": "air_defense",
                "location_name": "Riyadh",
                "location": WKTElement('POINT(46.6753 24.7136)', srid=4326),
                "description": "Saudi air defense forces intercepted ballistic missile targeting Riyadh. Debris fell in uninhabited area. No casualties reported.",
                "guidance": "Avoid area of debris. Follow Civil Defense instructions.",
                "detected_at": now - timedelta(hours=48),
                "confirmed_at": now - timedelta(hours=47, minutes=30),
                "reports_count": 25,
                "unique_sources_count": 10,
                "total_credibility": 450,
                "verification_method": "official_statement",
                "is_active": True,
                "region": "Riyadh",
                "country": "Saudi Arabia"
            },
            # 46 hours ago - Dhahran defense alert
            {
                "status": "LIKELY",
                "event_type": "air_defense",
                "location_name": "Dhahran",
                "location": WKTElement('POINT(50.0393 26.2361)', srid=4326),
                "description": "Air defense systems activated over Eastern Province. Possible drone incursion detected and engaged.",
                "guidance": "Remain indoors. Stay away from windows.",
                "detected_at": now - timedelta(hours=46),
                "confirmed_at": now - timedelta(hours=45),
                "reports_count": 8,
                "unique_sources_count": 4,
                "total_credibility": 180,
                "verification_method": "official_source",
                "is_active": False,
                "region": "Eastern Province",
                "country": "Saudi Arabia"
            },
            # 42 hours ago - Jeddah explosion reports
            {
                "status": "PROBABLE",
                "event_type": "explosion",
                "location_name": "Jeddah",
                "location": WKTElement('POINT(39.1925 21.4858)', srid=4326),
                "description": "Social media reports of loud explosion in Jeddah industrial area. Awaiting official confirmation.",
                "guidance": "Monitor official channels. Avoid speculation.",
                "detected_at": now - timedelta(hours=42),
                "confirmed_at": None,
                "reports_count": 5,
                "unique_sources_count": 3,
                "total_credibility": 75,
                "verification_method": "social_media",
                "is_active": False,
                "region": "Mecca Province",
                "country": "Saudi Arabia"
            },
            # 36 hours ago - Doha airport alert
            {
                "status": "CONFIRMED",
                "event_type": "drone",
                "location_name": "Doha",
                "location": WKTElement('POINT(51.5310 25.2854)', srid=4326),
                "description": "Qatar Civil Aviation confirms temporary airspace restriction near Hamad International Airport due to unauthorized drone activity. Airspace reopened after 45 minutes.",
                "guidance": "Airspace secure. Flight operations normal.",
                "detected_at": now - timedelta(hours=36),
                "confirmed_at": now - timedelta(hours=35),
                "reports_count": 15,
                "unique_sources_count": 6,
                "total_credibility": 300,
                "verification_method": "official_statement",
                "is_active": False,
                "region": "Doha",
                "country": "Qatar"
            },
            # 32 hours ago - Al Wakrah drone reports
            {
                "status": "LIKELY",
                "event_type": "drone",
                "location_name": "Al Wakrah",
                "location": WKTElement('POINT(51.5976 25.1659)', srid=4326),
                "description": "Multiple witnesses report drone sighting south of Doha near Al Wakrah. Security forces investigating.",
                "guidance": "Report any sightings to authorities. Do not approach.",
                "detected_at": now - timedelta(hours=32),
                "confirmed_at": None,
                "reports_count": 7,
                "unique_sources_count": 5,
                "total_credibility": 140,
                "verification_method": "witness_reports",
                "is_active": False,
                "region": "Al Wakrah",
                "country": "Qatar"
            },
            # 28 hours ago - Lusail alert drill
            {
                "status": "CONFIRMED",
                "event_type": "siren",
                "location_name": "Lusail",
                "location": WKTElement('POINT(51.5075 25.4175)', srid=4326),
                "description": "Emergency response drill conducted in Lusail City. Sirens and alerts were part of planned exercise.",
                "guidance": "This was a drill. No cause for concern.",
                "detected_at": now - timedelta(hours=28),
                "confirmed_at": now - timedelta(hours=28),
                "reports_count": 4,
                "unique_sources_count": 2,
                "total_credibility": 160,
                "verification_method": "official_announcement",
                "is_active": False,
                "region": "Lusail",
                "country": "Qatar"
            },
            # 24 hours ago - Qatar drone reports
            {
                "status": "PROBABLE",
                "event_type": "drone",
                "location_name": "Al Khor",
                "location": WKTElement('POINT(51.4969 25.6804)', srid=4326),
                "description": "Reports of unidentified drone activity north of Doha near Al Khor. Authorities aware and monitoring.",
                "guidance": "Remain calm. Report sightings. Do not engage.",
                "detected_at": now - timedelta(hours=24),
                "confirmed_at": None,
                "reports_count": 3,
                "unique_sources_count": 2,
                "total_credibility": 60,
                "verification_method": "eyewitness",
                "is_active": True,
                "region": "Al Khor",
                "country": "Qatar"
            },
            # 18 hours ago - Manama security alert
            {
                "status": "LIKELY",
                "event_type": "siren",
                "location_name": "Manama",
                "location": WKTElement('POINT(50.5860 26.2285)', srid=4326),
                "description": "Emergency sirens activated in Manama due to security alert. All clear given after investigation.",
                "guidance": "Situation resolved. Resume normal activities.",
                "detected_at": now - timedelta(hours=18),
                "confirmed_at": now - timedelta(hours=17, minutes=30),
                "reports_count": 6,
                "unique_sources_count": 3,
                "total_credibility": 130,
                "verification_method": "official_update",
                "is_active": False,
                "region": "Capital Governorate",
                "country": "Bahrain"
            },
            # 14 hours ago - Bahrain explosion
            {
                "status": "CONFIRMED",
                "event_type": "explosion",
                "location_name": "Muharraq",
                "location": WKTElement('POINT(50.6119 26.2575)', srid=4326),
                "description": "Small explosion reported at industrial facility in Muharraq. Civil Defense contained fire. No casualties. Under investigation.",
                "guidance": "Avoid the area. Investigation ongoing.",
                "detected_at": now - timedelta(hours=14),
                "confirmed_at": now - timedelta(hours=13),
                "reports_count": 10,
                "unique_sources_count": 5,
                "total_credibility": 220,
                "verification_method": "official_statement",
                "is_active": True,
                "region": "Muharraq",
                "country": "Bahrain"
            },
            # 12 hours ago - Bahrain siren test
            {
                "status": "CONFIRMED",
                "event_type": "siren",
                "location_name": "Riffa",
                "location": WKTElement('POINT(50.5550 26.1320)', srid=4326),
                "description": "Bahrain Civil Defense conducted emergency siren test in Riffa area as part of national preparedness program.",
                "guidance": "This was a scheduled test. No emergency.",
                "detected_at": now - timedelta(hours=12),
                "confirmed_at": now - timedelta(hours=12),
                "reports_count": 5,
                "unique_sources_count": 2,
                "total_credibility": 140,
                "verification_method": "official_announcement",
                "is_active": False,
                "region": "Southern Governorate",
                "country": "Bahrain"
            },
            # 6 hours ago - Recent Dubai alert
            {
                "status": "CONFIRMED",
                "event_type": "air_defense",
                "location_name": "Palm Jumeirah",
                "location": WKTElement('POINT(55.1284 25.1156)', srid=4326),
                "description": "Air defense activation over Palm Jumeirah. Hostile drone intercepted. Debris fell in sea. No injuries or damage.",
                "guidance": "Threat neutralized. Beaches temporarily closed for debris recovery.",
                "detected_at": now - timedelta(hours=6),
                "confirmed_at": now - timedelta(hours=5, minutes=45),
                "reports_count": 18,
                "unique_sources_count": 8,
                "total_credibility": 380,
                "verification_method": "multiple_official",
                "is_active": True,
                "region": "Dubai",
                "country": "UAE"
            },
            # 2 hours ago - Abu Dhabi airspace
            {
                "status": "LIKELY",
                "event_type": "drone",
                "location_name": "Al Ain",
                "location": WKTElement('POINT(55.8023 24.1302)', srid=4326),
                "description": "Reports of drone activity near Al Ain border area. UAE and Omani authorities coordinating response.",
                "guidance": "Avoid border areas. Follow instructions from security forces.",
                "detected_at": now - timedelta(hours=2),
                "confirmed_at": None,
                "reports_count": 4,
                "unique_sources_count": 3,
                "total_credibility": 110,
                "verification_method": "cross_border_coordination",
                "is_active": True,
                "region": "Al Ain",
                "country": "UAE"
            }
        ]
        
        created = []
        for incident_data in historical_incidents:
            incident = Incident(**incident_data)
            db.add(incident)
            created.append(incident)
        
        db.commit()
        
        # Count by country and status
        country_stats = {}
        status_stats = {}
        for inc in historical_incidents:
            country = inc.get("country", "Unknown")
            status = inc.get("status", "Unknown")
            country_stats[country] = country_stats.get(country, 0) + 1
            status_stats[status] = status_stats.get(status, 0) + 1
        
        return {
            "status": "success",
            "created": len(created),
            "time_span": "72 hours",
            "by_country": country_stats,
            "by_status": status_stats,
            "incidents": [{"id": str(i.id), "type": i.event_type, "location": i.location_name, "status": i.status} for i in created]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Historical data creation failed: {str(e)}")


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
    hours: int = Query(72, ge=1, le=168, description="Show incidents from last N hours"),
    db: Session = Depends(get_db)
):
    """Get all incidents from last 72 hours (active + recent for reference)"""
    incidents = IncidentCRUD.get_recent(db, hours=hours, limit=limit)
    
    # Convert to response format
    response = []
    for i in incidents:
        # Extract lat/lng from geography
        result = db.execute(
            text("SELECT ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng FROM incidents WHERE id = :id"),
            {'id': i.id}
        ).first()
        
        # Build source URL if we have external_id
        source_url = i.source_url
        if not source_url and i.external_id and i.source_platform == 'twitter':
            source_url = f"https://x.com/{i.source_handle}/status/{i.external_id}"
        
        response.append(IncidentResponse(
            id=str(i.id),
            status=i.status,
            event_type=i.event_type,
            classification=i.classification,
            location_name=i.location_name,
            country=i.country,
            lat=result.lat if result else 0,
            lng=result.lng if result else 0,
            distance_meters=None,
            description=i.description,
            guidance=i.guidance,
            detected_at=i.detected_at,
            reports_count=i.reports_count,
            unique_sources_count=i.unique_sources_count,
            media_urls=i.media_urls or [],
            source_name=i.source_name,
            source_handle=i.source_handle,
            source_platform=i.source_platform,
            source_url=source_url
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
        text("SELECT ST_Y(location::GEOMETRY) as lat, ST_X(location::GEOMETRY) as lng FROM incidents WHERE id = :id"),
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
