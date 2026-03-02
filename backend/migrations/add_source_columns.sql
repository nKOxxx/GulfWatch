-- Migration: Add source columns to incidents table
-- Run this if you get "column does not exist" errors

-- Add source info columns
ALTER TABLE incidents 
    ADD COLUMN IF NOT EXISTS source_handle VARCHAR(100),
    ADD COLUMN IF NOT EXISTS source_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS source_platform VARCHAR(50) DEFAULT 'twitter',
    ADD COLUMN IF NOT EXISTS external_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS source_url TEXT;

-- Make location nullable (for incidents without coordinates)
ALTER TABLE incidents 
    ALTER COLUMN location DROP NOT NULL;

-- Create index on source_handle for faster lookups
CREATE INDEX IF NOT EXISTS idx_incidents_source_handle ON incidents(source_handle);
