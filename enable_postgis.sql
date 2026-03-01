-- Enable PostGIS extension (run this on Render database)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify
SELECT PostGIS_Version();
