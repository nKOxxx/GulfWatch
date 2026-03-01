-- Gulf Watch Database Schema
-- PostgreSQL with PostGIS for geospatial queries

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- SOURCES (Official accounts, media, etc.)
-- ============================================
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    handle VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL, -- 'twitter', 'instagram', 'news', 'telegram'
    source_type VARCHAR(50) NOT NULL, -- 'ruler', 'government', 'civil_defense', 'police', 'media', 'user'
    credibility_score INTEGER DEFAULT 50, -- 0-100
    is_verified BOOLEAN DEFAULT false,
    is_official BOOLEAN DEFAULT false, -- Single source of truth
    country VARCHAR(100),
    region VARCHAR(100),
    follower_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(handle, platform)
);

-- Index for quick lookups
CREATE INDEX idx_sources_handle ON sources(handle, platform);
CREATE INDEX idx_sources_type ON sources(source_type);
CREATE INDEX idx_sources_official ON sources(is_official) WHERE is_official = true;

-- ============================================
-- INCIDENTS (Verified events)
-- ============================================
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event details
    status VARCHAR(20) NOT NULL CHECK (status IN ('UNCONFIRMED', 'PROBABLE', 'LIKELY', 'CONFIRMED', 'FALSE_ALARM', 'RESOLVED')),
    event_type VARCHAR(50) NOT NULL, -- 'air_defense', 'explosion', 'drone', 'siren', 'impact', 'other'
    classification VARCHAR(50), -- 'ballistic_missile', 'drone', 'cruise_missile', 'air_defense', 'unknown'
    
    -- Location
    location_name VARCHAR(200) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    location_accuracy_meters INTEGER DEFAULT 100,
    region VARCHAR(100),
    country VARCHAR(100),
    
    -- Content
    title VARCHAR(500),
    description TEXT,
    guidance TEXT, -- Official guidance text
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metrics
    reports_count INTEGER DEFAULT 0,
    unique_sources_count INTEGER DEFAULT 0,
    total_credibility INTEGER DEFAULT 0,
    
    -- Media
    media_urls TEXT[],
    
    -- Verification
    verified_by UUID REFERENCES sources(id),
    verification_method VARCHAR(50), -- 'single_official', 'multiple_sources', 'cross_reference', 'ai_analysis'
    
    -- For soft deletes/updates
    is_active BOOLEAN DEFAULT true,
    superseded_by UUID REFERENCES incidents(id)
);

-- Geospatial indexes
CREATE INDEX idx_incidents_location ON incidents USING GIST(location);
CREATE INDEX idx_incidents_status ON incidents(status) WHERE is_active = true;
CREATE INDEX idx_incidents_time ON incidents(detected_at);
CREATE INDEX idx_incidents_region ON incidents(region, country);
CREATE INDEX idx_incidents_type ON incidents(event_type);

-- ============================================
-- RAW REPORTS (Before verification)
-- ============================================
CREATE TABLE raw_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source
    source_id UUID REFERENCES sources(id),
    external_id VARCHAR(200), -- Tweet ID, etc.
    
    -- Content
    content TEXT NOT NULL,
    content_language VARCHAR(10) DEFAULT 'en',
    
    -- Location (extracted from text)
    location_text VARCHAR(200),
    location GEOGRAPHY(POINT, 4326),
    location_confidence DECIMAL(3,2), -- 0.0 to 1.0
    
    -- Metadata from source
    source_credibility INTEGER DEFAULT 0,
    follower_count INTEGER DEFAULT 0,
    is_verified_source BOOLEAN DEFAULT false,
    
    -- Media
    media_urls TEXT[],
    
    -- Timestamps
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Processing
    processed BOOLEAN DEFAULT false,
    linked_incident UUID REFERENCES incidents(id),
    processing_metadata JSONB DEFAULT '{}',
    
    -- Raw data
    raw_data JSONB NOT NULL
);

CREATE INDEX idx_raw_reports_source ON raw_reports(source_id);
CREATE INDEX idx_raw_reports_processed ON raw_reports(processed) WHERE processed = false;
CREATE INDEX idx_raw_reports_incident ON raw_reports(linked_incident);
CREATE INDEX idx_raw_reports_time ON raw_reports(posted_at);
CREATE INDEX idx_raw_reports_location ON raw_reports USING GIST(location);

-- ============================================
-- VERIFICATION LOG (Audit trail)
-- ============================================
CREATE TABLE verification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    
    -- What changed
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    
    -- Why it changed
    reason TEXT NOT NULL,
    method VARCHAR(50), -- 'official_source', 'clustering', 'cross_reference', 'manual_review'
    
    -- Sources involved
    source_reports UUID[], -- Array of raw_reports.id
    
    -- Who/what triggered it
    triggered_by VARCHAR(50), -- 'system', 'admin', 'api'
    triggered_by_user UUID, -- If manual
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_verification_logs_incident ON verification_logs(incident_id);
CREATE INDEX idx_verification_logs_time ON verification_logs(created_at);

-- ============================================
-- USER LOCATIONS (For notifications - anonymous)
-- ============================================
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Anonymous identifier (device token or generated)
    subscription_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Location preferences
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    location_name VARCHAR(200),
    radius_km INTEGER DEFAULT 50,
    
    -- Notification preferences
    notify_confirmed BOOLEAN DEFAULT true,
    notify_likely BOOLEAN DEFAULT true,
    notify_probable BOOLEAN DEFAULT false,
    
    -- Device info
    platform VARCHAR(50), -- 'web', 'ios', 'android'
    push_token TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_location ON user_subscriptions USING GIST(location);
CREATE INDEX idx_subscriptions_active ON user_subscriptions(is_active) WHERE is_active = true;

-- ============================================
-- NOTIFICATIONS LOG
-- ============================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID REFERENCES user_subscriptions(id) ON DELETE CASCADE,
    incident_id UUID REFERENCES incidents(id),
    
    -- Content
    title VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    
    -- Status
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notifications_subscription ON notifications(subscription_id);
CREATE INDEX idx_notifications_incident ON notifications(incident_id);

-- ============================================
-- SYSTEM METRICS (Optional but useful)
-- ============================================
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 4),
    metric_unit VARCHAR(50),
    labels JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metrics_name ON system_metrics(metric_name, recorded_at);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_incidents_updated_at BEFORE UPDATE ON incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to find incidents near a point
CREATE OR REPLACE FUNCTION get_incidents_near_location(
    lat DECIMAL,
    lng DECIMAL,
    radius_km DECIMAL,
    min_status VARCHAR DEFAULT 'PROBABLE'
)
RETURNS TABLE (
    id UUID,
    status VARCHAR,
    event_type VARCHAR,
    location_name VARCHAR,
    distance_meters DECIMAL,
    detected_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    point GEOGRAPHY;
BEGIN
    point := ST_SetSRID(ST_MakePoint(lng, lat), 4326)::GEOGRAPHY;
    
    RETURN QUERY
    SELECT 
        i.id,
        i.status,
        i.event_type,
        i.location_name,
        ST_Distance(i.location, point) as distance_meters,
        i.detected_at
    FROM incidents i
    WHERE i.is_active = true
      AND i.status NOT IN ('FALSE_ALARM', 'RESOLVED')
      AND (
          min_status = 'UNCONFIRMED' OR
          (min_status = 'PROBABLE' AND i.status IN ('PROBABLE', 'LIKELY', 'CONFIRMED')) OR
          (min_status = 'LIKELY' AND i.status IN ('LIKELY', 'CONFIRMED')) OR
          (min_status = 'CONFIRMED' AND i.status = 'CONFIRMED')
      )
      AND ST_DWithin(i.location, point, radius_km * 1000)
    ORDER BY ST_Distance(i.location, point);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate distance between two points
CREATE OR REPLACE FUNCTION calculate_distance_km(
    lat1 DECIMAL,
    lng1 DECIMAL,
    lat2 DECIMAL,
    lng2 DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
    point1 GEOGRAPHY;
    point2 GEOGRAPHY;
BEGIN
    point1 := ST_SetSRID(ST_MakePoint(lng1, lat1), 4326)::GEOGRAPHY;
    point2 := ST_SetSRID(ST_MakePoint(lng2, lat2), 4326)::GEOGRAPHY;
    RETURN ST_Distance(point1, point2) / 1000;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- INITIAL DATA (UAE Official Sources)
-- ============================================

INSERT INTO sources (name, handle, platform, source_type, credibility_score, is_verified, is_official, country, follower_count) VALUES
-- Rulers
('HH Sheikh Mohamed bin Zayed Al Nahyan', 'mohamedbinzayed', 'twitter', 'ruler', 100, true, true, 'UAE', 5000000),
('HH Sheikh Mohammed bin Rashid Al Maktoum', 'hhshkmohd', 'twitter', 'ruler', 100, true, true, 'UAE', 11000000),
('HH Sheikh Dr. Sultan bin Muhammad Al Qasimi', 'sultanalqasimi', 'twitter', 'ruler', 100, true, true, 'UAE', 2000000),

-- Federal Government
('UAE Government', 'uaegov', 'twitter', 'government', 100, true, true, 'UAE', 1200000),
('WAM News Agency', 'wamnews', 'twitter', 'state_media', 100, true, true, 'UAE', 500000),
('Ministry of Interior UAE', 'moiuae', 'twitter', 'security', 100, true, true, 'UAE', 800000),
('UAE Civil Defense', 'uae_cd', 'twitter', 'civil_defense', 100, true, true, 'UAE', 300000),
('NCEMA UAE', 'ncema_uae', 'twitter', 'emergency_management', 100, true, true, 'UAE', 400000),

-- Dubai
('Dubai Media Office', 'dxbmediaoffice', 'twitter', 'media_office', 95, true, true, 'UAE', 1500000),
('Dubai Police', 'dubaipolicehq', 'twitter', 'police', 100, true, true, 'UAE', 600000),
('Dubai Civil Defense', 'dubai_civildef', 'twitter', 'civil_defense', 100, true, true, 'UAE', 200000),

-- Abu Dhabi
('Abu Dhabi Media Office', 'admediaoffice', 'twitter', 'media_office', 95, true, true, 'UAE', 800000),
('Abu Dhabi Police', 'ad_policehq', 'twitter', 'police', 100, true, true, 'UAE', 400000),
('Abu Dhabi Government', 'abudhabi_gov', 'twitter', 'government', 100, true, true, 'UAE', 500000),

-- Verified Media
('Gulf News', 'gulf_news', 'twitter', 'media', 90, true, false, 'UAE', 1500000),
('The National UAE', 'thenationaluae', 'twitter', 'media', 90, true, false, 'UAE', 800000),
('Khaleej Times', 'khaleejtimes', 'twitter', 'media', 90, true, false, 'UAE', 700000)
ON CONFLICT (handle, platform) DO NOTHING;

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Active incidents with full details
CREATE VIEW active_incidents AS
SELECT 
    i.*,
    ST_Y(i.location::GEOMETRY) as lat,
    ST_X(i.location::GEOMETRY) as lng
FROM incidents i
WHERE i.is_active = true
  AND i.status NOT IN ('FALSE_ALARM', 'RESOLVED');

-- Recent incidents (last 24 hours)
CREATE VIEW recent_incidents AS
SELECT * FROM incidents
WHERE detected_at > NOW() - INTERVAL '24 hours'
ORDER BY detected_at DESC;

-- Official sources only
CREATE VIEW official_sources AS
SELECT * FROM sources WHERE is_official = true AND is_active = true;

-- Pending raw reports
CREATE VIEW pending_reports AS
SELECT * FROM raw_reports WHERE processed = false;
