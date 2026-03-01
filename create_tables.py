import psycopg2

DATABASE_URL = "postgresql://gulf_watch_db_user:tfhqXXT4KA0PwyjvN3qheJun7r5cBvxT@dpg-d6i69q1drdic73d0g6m0-a.frankfurt-postgres.render.com/gulf_watch_db"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create sources table
print("Creating sources table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    handle VARCHAR(100) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    credibility_score INTEGER DEFAULT 50,
    is_verified BOOLEAN DEFAULT false,
    is_official BOOLEAN DEFAULT false,
    country VARCHAR(100),
    region VARCHAR(100),
    follower_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(handle, platform)
);
""")

# Create incidents table
print("Creating incidents table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    classification VARCHAR(50),
    location_name VARCHAR(200) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    location_accuracy_meters INTEGER DEFAULT 100,
    region VARCHAR(100),
    country VARCHAR(100),
    title VARCHAR(500),
    description TEXT,
    guidance TEXT,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reports_count INTEGER DEFAULT 0,
    unique_sources_count INTEGER DEFAULT 0,
    total_credibility INTEGER DEFAULT 0,
    media_urls TEXT[],
    verified_by UUID,
    verification_method VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    superseded_by UUID
);
""")

# Insert official UAE sources
print("Inserting UAE official sources...")
cur.execute("""
INSERT INTO sources (name, handle, platform, source_type, credibility_score, is_verified, is_official, country, follower_count) VALUES
('HH Sheikh Mohamed bin Zayed Al Nahyan', 'mohamedbinzayed', 'twitter', 'ruler', 100, true, true, 'UAE', 5000000),
('HH Sheikh Mohammed bin Rashid Al Maktoum', 'hhshkmohd', 'twitter', 'ruler', 100, true, true, 'UAE', 11000000),
('UAE Government', 'uaegov', 'twitter', 'government', 100, true, true, 'UAE', 1200000),
('WAM News Agency', 'WAMnews', 'twitter', 'state_media', 100, true, true, 'UAE', 500000),
('Ministry of Interior UAE', 'moiuae', 'twitter', 'security', 100, true, true, 'UAE', 800000),
('UAE Civil Defense', 'uae_cd', 'twitter', 'civil_defense', 100, true, true, 'UAE', 300000),
('NCEMA UAE', 'ncema_uae', 'twitter', 'emergency_management', 100, true, true, 'UAE', 400000),
('Dubai Police', 'dubaipolicehq', 'twitter', 'police', 100, true, true, 'UAE', 600000),
('Dubai Civil Defense', 'dubai_civildef', 'twitter', 'civil_defense', 100, true, true, 'UAE', 200000),
('Gulf News', 'gulf_news', 'twitter', 'media', 90, true, false, 'UAE', 1500000)
ON CONFLICT (handle, platform) DO NOTHING;
""")

conn.commit()
print("✅ Tables created and sources inserted!")

cur.close()
conn.close()
