"""
Database models and connection for Gulf Watch
Uses SQLAlchemy with PostgreSQL and PostGIS
"""

import os
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean, 
    DateTime, Text, ARRAY, ForeignKey, JSON, DECIMAL,
    Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.sql import func
from geoalchemy2 import Geometry, Geography

# Database URL from environment or default
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'postgresql://gulfwatch:gulfwatch@localhost:5432/gulfwatch'
)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Base class
Base = declarative_base()

# ============================================
# MODELS
# ============================================

class Source(Base):
    """Official and unofficial sources"""
    __tablename__ = 'sources'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    handle = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)  # twitter, instagram, news
    source_type = Column(String(50), nullable=False)  # ruler, government, media
    credibility_score = Column(Integer, default=50)
    is_verified = Column(Boolean, default=False)
    is_official = Column(Boolean, default=False)
    country = Column(String(100))
    region = Column(String(100))
    follower_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    raw_reports = relationship("RawReport", back_populates="source")
    
    __table_args__ = (
        UniqueConstraint('handle', 'platform', name='unique_source_handle'),
        Index('idx_sources_handle', 'handle', 'platform'),
        Index('idx_sources_official', 'is_official'),
    )
    
    @property
    def is_single_source_trusted(self) -> bool:
        """Can this source be trusted as single source of truth?"""
        return self.is_official and self.credibility_score >= 100


class Incident(Base):
    """Verified/aggregated incidents"""
    __tablename__ = 'incidents'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    status = Column(String(20), nullable=False)  # UNCONFIRMED, PROBABLE, LIKELY, CONFIRMED, FALSE_ALARM, RESOLVED
    event_type = Column(String(50), nullable=False)  # air_defense, explosion, drone, etc.
    classification = Column(String(50))  # ballistic_missile, drone, etc.
    
    # Location
    location_name = Column(String(200), nullable=False)
    location = Column(Geography('POINT', srid=4326), nullable=False)
    location_accuracy_meters = Column(Integer, default=100)
    region = Column(String(100))
    country = Column(String(100))
    
    # Content
    title = Column(String(500))
    description = Column(Text)
    guidance = Column(Text)  # Official guidance
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), nullable=False)
    confirmed_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Metrics
    reports_count = Column(Integer, default=0)
    unique_sources_count = Column(Integer, default=0)
    total_credibility = Column(Integer, default=0)
    
    # Media
    media_urls = Column(ARRAY(Text), default=[])
    
    # Verification
    verified_by = Column(PGUUID(as_uuid=True), ForeignKey('sources.id'))
    verification_method = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    superseded_by = Column(PGUUID(as_uuid=True), ForeignKey('incidents.id'))
    
    # Relationships
    raw_reports = relationship("RawReport", back_populates="incident")
    verification_logs = relationship("VerificationLog", back_populates="incident")
    
    __table_args__ = (
        Index('idx_incidents_status', 'status'),
        Index('idx_incidents_time', 'detected_at'),
        Index('idx_incidents_location', 'location', postgresql_using='GIST'),
        Index('idx_incidents_region', 'region', 'country'),
    )
    
    @property
    def lat(self) -> Optional[float]:
        """Extract latitude from geography"""
        # Will be populated by query
        return None
    
    @property
    def lng(self) -> Optional[float]:
        """Extract longitude from geography"""
        return None


class RawReport(Base):
    """Individual reports before verification"""
    __tablename__ = 'raw_reports'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(PGUUID(as_uuid=True), ForeignKey('sources.id'))
    external_id = Column(String(200))  # Tweet ID, etc.
    
    content = Column(Text, nullable=False)
    content_language = Column(String(10), default='en')
    
    location_text = Column(String(200))
    location = Column(Geography('POINT', srid=4326))
    location_confidence = Column(DECIMAL(3, 2))
    
    source_credibility = Column(Integer, default=0)
    follower_count = Column(Integer, default=0)
    is_verified_source = Column(Boolean, default=False)
    
    media_urls = Column(ARRAY(Text), default=[])
    
    posted_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=func.now())
    
    processed = Column(Boolean, default=False)
    linked_incident = Column(PGUUID(as_uuid=True), ForeignKey('incidents.id'))
    processing_metadata = Column(JSONB, default={})
    raw_data = Column(JSONB, nullable=False)
    
    # Relationships
    source = relationship("Source", back_populates="raw_reports")
    incident = relationship("Incident", back_populates="raw_reports")
    
    __table_args__ = (
        Index('idx_raw_reports_processed', 'processed'),
        Index('idx_raw_reports_time', 'posted_at'),
        Index('idx_raw_reports_source', 'source_id'),
    )


class VerificationLog(Base):
    """Audit trail for verification changes"""
    __tablename__ = 'verification_logs'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id = Column(PGUUID(as_uuid=True), ForeignKey('incidents.id', ondelete='CASCADE'))
    
    previous_status = Column(String(20))
    new_status = Column(String(20))
    reason = Column(Text, nullable=False)
    method = Column(String(50))
    source_reports = Column(ARRAY(PGUUID(as_uuid=True)))
    triggered_by = Column(String(50))
    triggered_by_user = Column(PGUUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    incident = relationship("Incident", back_populates="verification_logs")
    
    __table_args__ = (
        Index('idx_verification_logs_incident', 'incident_id'),
    )


class UserSubscription(Base):
    """Anonymous user subscriptions for notifications"""
    __tablename__ = 'user_subscriptions'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_token = Column(String(255), unique=True, nullable=False)
    
    location = Column(Geography('POINT', srid=4326), nullable=False)
    location_name = Column(String(200))
    radius_km = Column(Integer, default=50)
    
    notify_confirmed = Column(Boolean, default=True)
    notify_likely = Column(Boolean, default=True)
    notify_probable = Column(Boolean, default=False)
    
    platform = Column(String(50))  # web, ios, android
    push_token = Column(Text)
    
    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True), default=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    __table_args__ = (
        Index('idx_subscriptions_active', 'is_active'),
        Index('idx_subscriptions_location', 'location', postgresql_using='GIST'),
    )


class Notification(Base):
    """Notification log"""
    __tablename__ = 'notifications'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(PGUUID(as_uuid=True), ForeignKey('user_subscriptions.id', ondelete='CASCADE'))
    incident_id = Column(PGUUID(as_uuid=True), ForeignKey('incidents.id'))
    
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    __table_args__ = (
        Index('idx_notifications_subscription', 'subscription_id'),
    )


# ============================================
# DATABASE FUNCTIONS
# ============================================

def init_database():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (use as FastAPI dependency)"""
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()


# ============================================
# CRUD OPERATIONS
# ============================================

class IncidentCRUD:
    """CRUD operations for incidents"""
    
    @staticmethod
    def create(db: Session, **kwargs) -> Incident:
        """Create new incident"""
        incident = Incident(**kwargs)
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident
    
    @staticmethod
    def get_active(db: Session, limit: int = 100) -> List[Incident]:
        """Get all active incidents"""
        return db.query(Incident).filter(
            Incident.is_active == True,
            Incident.status.notin_(['FALSE_ALARM', 'RESOLVED'])
        ).order_by(Incident.detected_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, incident_id: UUID) -> Optional[Incident]:
        """Get incident by ID"""
        return db.query(Incident).filter(Incident.id == incident_id).first()
    
    @staticmethod
    def get_near_location(
        db: Session, 
        lat: float, 
        lng: float, 
        radius_km: float = 50,
        min_status: str = 'PROBABLE'
    ) -> List[dict]:
        """Get incidents near a location using PostGIS"""
        # Use raw SQL for geospatial query
        status_filter = {
            'UNCONFIRMED': "AND 1=1",  # All except resolved
            'PROBABLE': "AND i.status IN ('PROBABLE', 'LIKELY', 'CONFIRMED')",
            'LIKELY': "AND i.status IN ('LIKELY', 'CONFIRMED')",
            'CONFIRMED': "AND i.status = 'CONFIRMED'"
        }.get(min_status, "AND i.status IN ('PROBABLE', 'LIKELY', 'CONFIRMED')")
        
        query = f"""
        SELECT 
            i.id,
            i.status,
            i.event_type,
            i.location_name,
            i.description,
            i.detected_at,
            i.guidance,
            i.media_urls,
            i.reports_count,
            i.unique_sources_count,
            ST_Distance(i.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::GEOGRAPHY) as distance_meters,
            ST_Y(i.location::GEOMETRY) as lat,
            ST_X(i.location::GEOMETRY) as lng
        FROM incidents i
        WHERE i.is_active = true
          AND i.status NOT IN ('FALSE_ALARM', 'RESOLVED')
          {status_filter}
          AND ST_DWithin(i.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::GEOGRAPHY, :radius)
        ORDER BY ST_Distance(i.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::GEOGRAPHY)
        """
        
        result = db.execute(query, {
            'lat': lat,
            'lng': lng,
            'radius': radius_km * 1000
        })
        
        return [dict(row) for row in result]
    
    @staticmethod
    def update_status(
        db: Session, 
        incident_id: UUID, 
        new_status: str,
        reason: str,
        method: str = 'manual'
    ) -> Incident:
        """Update incident status with audit log"""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
        
        old_status = incident.status
        incident.status = new_status
        
        # Add verification log
        log = VerificationLog(
            incident_id=incident_id,
            previous_status=old_status,
            new_status=new_status,
            reason=reason,
            method=method,
            triggered_by='system'
        )
        db.add(log)
        db.commit()
        db.refresh(incident)
        return incident


class SourceCRUD:
    """CRUD operations for sources"""
    
    @staticmethod
    def get_by_handle(db: Session, handle: str, platform: str) -> Optional[Source]:
        """Get source by handle and platform"""
        return db.query(Source).filter(
            Source.handle == handle,
            Source.platform == platform
        ).first()
    
    @staticmethod
    def get_official_sources(db: Session) -> List[Source]:
        """Get all official (single source of truth) sources"""
        return db.query(Source).filter(
            Source.is_official == True,
            Source.is_active == True
        ).all()
    
    @staticmethod
    def get_trusted_single_source(db: Session) -> List[Source]:
        """Get sources that can be trusted as single source"""
        return db.query(Source).filter(
            Source.is_official == True,
            Source.credibility_score >= 100,
            Source.is_active == True
        ).all()


class RawReportCRUD:
    """CRUD operations for raw reports"""
    
    @staticmethod
    def create(db: Session, **kwargs) -> RawReport:
        """Create new raw report"""
        report = RawReport(**kwargs)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_unprocessed(db: Session, limit: int = 100) -> List[RawReport]:
        """Get unprocessed reports for verification"""
        return db.query(RawReport).filter(
            RawReport.processed == False
        ).order_by(RawReport.posted_at.desc()).limit(limit).all()
    
    @staticmethod
    def link_to_incident(
        db: Session, 
        report_id: UUID, 
        incident_id: UUID,
        processed: bool = True
    ):
        """Link a raw report to an incident"""
        report = db.query(RawReport).filter(RawReport.id == report_id).first()
        if report:
            report.linked_incident = incident_id
            report.processed = processed
            db.commit()


class SubscriptionCRUD:
    """CRUD operations for user subscriptions"""
    
    @staticmethod
    def create_or_update(
        db: Session, 
        token: str, 
        lat: float, 
        lng: float,
        **kwargs
    ) -> UserSubscription:
        """Create or update subscription"""
        from geoalchemy2.elements import WKTElement
        
        # Check if exists
        sub = db.query(UserSubscription).filter(
            UserSubscription.subscription_token == token
        ).first()
        
        if sub:
            # Update
            sub.location = WKTElement(f'POINT({lng} {lat})', srid=4326)
            sub.last_active_at = func.now()
            for key, value in kwargs.items():
                setattr(sub, key, value)
        else:
            # Create new
            sub = UserSubscription(
                subscription_token=token,
                location=WKTElement(f'POINT({lng} {lat})', srid=4326),
                **kwargs
            )
            db.add(sub)
        
        db.commit()
        db.refresh(sub)
        return sub
    
    @staticmethod
    def get_near_incident(
        db: Session, 
        incident_id: UUID,
        status: str
    ) -> List[UserSubscription]:
        """Get subscriptions that should be notified about an incident"""
        # Get incident location
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return []
        
        # Determine minimum status for notification
        status_priority = {
            'CONFIRMED': ['notify_confirmed'],
            'LIKELY': ['notify_likely', 'notify_confirmed'],
            'PROBABLE': ['notify_probable', 'notify_likely', 'notify_confirmed']
        }
        
        notification_prefs = status_priority.get(status, ['notify_confirmed'])
        
        # Query subscriptions near incident
        query = f"""
        SELECT s.*
        FROM user_subscriptions s
        WHERE s.is_active = true
          AND ST_DWithin(s.location, :incident_location, s.radius_km * 1000)
          AND ({' OR '.join(f's.{pref} = true' for pref in notification_prefs)})
        """
        
        result = db.execute(query, {'incident_location': incident.location})
        return [dict(row) for row in result]


# ============================================
# UTILITY FUNCTIONS
# ============================================

def calculate_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points using PostGIS"""
    from sqlalchemy import text
    
    result = engine.execute(
        text("SELECT calculate_distance_km(:lat1, :lng1, :lat2, :lng2)"),
        {'lat1': lat1, 'lng1': lng1, 'lat2': lat2, 'lng2': lng2}
    ).scalar()
    
    return float(result) if result else 0.0


if __name__ == "__main__":
    # Initialize database
    print("Creating database tables...")
    init_database()
    print("Database initialized!")
    
    # Test connection
    db = Session(bind=engine)
    official_count = db.query(Source).filter(Source.is_official == True).count()
    print(f"Official sources in database: {official_count}")
    db.close()
