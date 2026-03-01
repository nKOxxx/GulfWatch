import { Pool, PoolClient } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'gulfwatch',
  user: process.env.DB_USER || 'gulfwatch',
  password: process.env.DB_PASSWORD || 'password',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

export const db = {
  query: (text: string, params?: any[]) => pool.query(text, params),
  
  getClient: (): Promise<PoolClient> => pool.connect(),
  
  healthCheck: async (): Promise<boolean> => {
    try {
      await pool.query('SELECT 1');
      return true;
    } catch {
      return false;
    }
  },
  
  // Region queries
  getRegions: async () => {
    const result = await pool.query(
      `SELECT id, name, country, code, 
              ST_Y(center::geometry) as lat, 
              ST_X(center::geometry) as lng,
              timezone
       FROM regions WHERE is_active = true`
    );
    return result.rows;
  },
  
  getRegionByCode: async (code: string) => {
    const result = await pool.query(
      `SELECT * FROM regions WHERE code = $1 AND is_active = true`,
      [code.toUpperCase()]
    );
    return result.rows[0];
  },
  
  // Incident queries
  getIncidents: async (regionId: string, limit: number = 50) => {
    const result = await pool.query(
      `SELECT i.*, 
              ST_Y(location::geometry) as lat, 
              ST_X(location::geometry) as lng,
              r.name as region_name
       FROM incidents i
       JOIN regions r ON i.region_id = r.id
       WHERE i.region_id = $1 
       ORDER BY i.detected_at DESC
       LIMIT $2`,
      [regionId, limit]
    );
    return result.rows;
  },
  
  getActiveIncidents: async (regionId: string) => {
    const result = await pool.query(
      `SELECT i.*, 
              ST_Y(location::geometry) as lat, 
              ST_X(location::geometry) as lng
       FROM incidents i
       WHERE i.region_id = $1 AND i.status = 'active'
       ORDER BY i.severity DESC, i.detected_at DESC`,
      [regionId]
    );
    return result.rows;
  },
  
  // Raw events
  createRawEvent: async (event: {
    sourceId: string;
    regionId: string;
    eventType: string;
    location: { lat: number; lng: number };
    detectedAt: Date;
    rawData: any;
    mediaUrls?: string[];
    textContent?: string;
  }) => {
    const result = await pool.query(
      `INSERT INTO raw_events 
       (source_id, region_id, event_type, location, detected_at, raw_data, media_urls, text_content)
       VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326)::geography, $6, $7, $8, $9)
       RETURNING *`,
      [
        event.sourceId,
        event.regionId,
        event.eventType,
        event.location.lng,
        event.location.lat,
        event.detectedAt,
        JSON.stringify(event.rawData),
        event.mediaUrls || [],
        event.textContent
      ]
    );
    return result.rows[0];
  },
  
  // Data sources
  getSourcesByRegion: async (regionId: string) => {
    const result = await pool.query(
      `SELECT s.*, 
              ST_Y(location::geometry) as lat, 
              ST_X(location::geometry) as lng
       FROM data_sources s
       WHERE s.region_id = $1 AND s.is_active = true`,
      [regionId]
    );
    return result.rows;
  },
  
  // Verification
  updateEventVerification: async (eventId: string, status: string, score: number) => {
    await pool.query(
      `UPDATE raw_events SET verification_status = $1, verification_score = $2 WHERE id = $3`,
      [status, score, eventId]
    );
  },
  
  // Camera partnerships
  getPartnerships: async () => {
    const result = await pool.query(
      `SELECT * FROM camera_partnerships ORDER BY created_at DESC`
    );
    return result.rows;
  },
  
  createPartnership: async (partnership: {
    organizationName: string;
    organizationType: string;
    contactEmail: string;
    cameraCount: number;
    regions: string[];
  }) => {
    const result = await pool.query(
      `INSERT INTO camera_partnerships 
       (organization_name, organization_type, contact_email, camera_count, regions)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [
        partnership.organizationName,
        partnership.organizationType,
        partnership.contactEmail,
        partnership.cameraCount,
        partnership.regions
      ]
    );
    return result.rows[0];
  }
};
