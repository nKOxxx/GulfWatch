-- Gulf Watch Database Schema
-- PostgreSQL with PostGIS extension

-- Enable PostGIS for geospatial queries
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Regions table (Dubai, Abu Dhabi, Bahrain, etc.)
CREATE TABLE regions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL, -- e.g., 'DXB', 'AUH', 'BAH'
    geometry GEOGRAPHY(POLYGON, 4326) NOT NULL, -- Boundary
    center GEOGRAPHY(POINT, 4326) NOT NULL, -- Center point
    timezone VARCHAR(50) DEFAULT 'Asia/Dubai',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data sources (cameras, social media, news, etc.)
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'camera', 'social_media', 'news', 'seismic', 'government', 'private'
    subtype VARCHAR(50), -- 'twitter', 'telegram', 'rta_camera', 'private_camera', etc.
    region_id UUID REFERENCES regions(id),
    location GEOGRAPHY(POINT, 4326), -- For cameras/sensors
    coverage_radius_meters INTEGER, -- Camera view range
    direction_degrees INTEGER, -- Camera facing direction (0-360)
    url TEXT, -- API endpoint or stream URL
    api_key_encrypted TEXT, -- Encrypted credentials
    reliability_score DECIMAL(3,2) DEFAULT 0.5, -- 0.0 to 1.0
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false, -- Public vs private source
    partner_organization VARCHAR(200), -- For government/private partnerships
    rate_limit_per_minute INTEGER DEFAULT 60,
    metadata JSONB, -- Flexible config per source type
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Raw events (before verification)
CREATE TABLE raw_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES data_sources(id),
    region_id UUID REFERENCES regions(id),
    event_type VARCHAR(50) NOT NULL, -- 'explosion', 'drone_sighting', 'siren', 'aircraft', 'impact'
    location GEOGRAPHY(POINT, 4326),
    location_accuracy_meters INTEGER DEFAULT 100,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_data JSONB NOT NULL, -- Original data
    media_urls TEXT[], -- Photos, videos
    text_content TEXT, -- Tweet text, description
    language VARCHAR(10) DEFAULT 'en',
    verification_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'verified', 'rejected', 'uncertain'
    verification_score DECIMAL(3,2), -- AI confidence score
    duplicate_of UUID REFERENCES raw_events(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Verification results
CREATE TABLE verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES raw_events(id),
    method VARCHAR(50) NOT NULL, -- 'cross_reference', 'ai_analysis', 'human_review', 'sensor_correlation'
    score DECIMAL(3,2) NOT NULL, -- 0.0 to 1.0
    confidence VARCHAR(20), -- 'low', 'medium', 'high', 'certain'
    details JSONB, -- Method-specific results
    verified_by UUID, -- User ID if human review
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Confirmed incidents (after verification)
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id UUID REFERENCES regions(id),
    event_type VARCHAR(50) NOT NULL,
    classification VARCHAR(50), -- 'ballistic_missile', 'drone', 'air_defense', 'unknown'
    location GEOGRAPHY(POINT, 4326),
    location_accuracy_meters INTEGER,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'false_alarm'
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    source_events UUID[], -- Array of raw_event IDs that contributed
    description TEXT,
    media_urls TEXT[],
    impact_assessment JSONB, -- Damage, casualties, etc.
    trajectory GEOGRAPHY(LINESTRING, 4326), -- If tracked
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts sent to users
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id),
    region_id UUID REFERENCES regions(id),
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    channels TEXT[], -- 'push', 'sms', 'telegram', 'email'
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0
);

-- Camera partnerships (track status)
CREATE TABLE camera_partnerships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_name VARCHAR(200) NOT NULL,
    organization_type VARCHAR(50), -- 'government', 'private', 'critical_infrastructure', 'individual'
    contact_email VARCHAR(200),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'negotiating', 'active', 'inactive'
    camera_count INTEGER DEFAULT 0,
    regions UUID[], -- Which regions covered
    agreement_signed BOOLEAN DEFAULT false,
    data_sharing_terms TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users and subscriptions
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE,
    phone_number VARCHAR(20),
    email VARCHAR(200),
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    region_id UUID REFERENCES regions(id),
    location GEOGRAPHY(POINT, 4326), -- Specific location within region
    alert_radius_meters INTEGER DEFAULT 5000, -- Alert within this radius
    min_severity VARCHAR(20) DEFAULT 'medium', -- Only alert for this severity and above
    channels TEXT[] DEFAULT ARRAY['push'], -- Preferred alert channels
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_raw_events_region ON raw_events(region_id);
CREATE INDEX idx_raw_events_location ON raw_events USING GIST(location);
CREATE INDEX idx_raw_events_detected_at ON raw_events(detected_at);
CREATE INDEX idx_raw_events_verification ON raw_events(verification_status);
CREATE INDEX idx_incidents_region ON incidents(region_id);
CREATE INDEX idx_incidents_location ON incidents USING GIST(location);
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at);
CREATE INDEX idx_data_sources_region ON data_sources(region_id);
CREATE INDEX idx_data_sources_type ON data_sources(type);

-- Insert initial regions
INSERT INTO regions (name, country, code, geometry, center, timezone) VALUES
('Dubai', 'United Arab Emirates', 'DXB', 
 ST_MakeEnvelope(54.8, 24.7, 55.5, 25.5, 4326)::geography,
 ST_SetSRID(ST_MakePoint(55.2708, 25.2048), 4326)::geography,
 'Asia/Dubai'),
('Abu Dhabi', 'United Arab Emirates', 'AUH',
 ST_MakeEnvelope(54.2, 23.9, 55.0, 24.8, 4326)::geography,
 ST_SetSRID(ST_MakePoint(54.3773, 24.4539), 4326)::geography,
 'Asia/Dubai'),
('Sharjah', 'United Arab Emirates', 'SHJ',
 ST_MakeEnvelope(55.3, 24.9, 55.8, 25.6, 4326)::geography,
 ST_SetSRID(ST_MakePoint(55.4033, 25.3573), 4326)::geography,
 'Asia/Dubai'),
('Manama', 'Bahrain', 'BAH',
 ST_MakeEnvelope(50.4, 25.9, 50.9, 26.4, 4326)::geography,
 ST_SetSRID(ST_MakePoint(50.5860, 26.2285), 4326)::geography,
 'Asia/Bahrain'),
('Doha', 'Qatar', 'DOH',
 ST_MakeEnvelope(51.2, 24.5, 51.8, 25.5, 4326)::geography,
 ST_SetSRID(ST_MakePoint(51.5310, 25.2854), 4326)::geography,
 'Asia/Qatar'),
('Riyadh', 'Saudi Arabia', 'RUH',
 ST_MakeEnvelope(46.3, 24.3, 47.0, 25.0, 4326)::geography,
 ST_SetSRID(ST_MakePoint(46.6753, 24.7136), 4326)::geography,
 'Asia/Riyadh');
