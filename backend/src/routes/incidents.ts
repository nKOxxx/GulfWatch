import { Router } from 'express';
import { db } from '../services/database';

export const incidentsRouter = Router();

// GET /api/incidents?region=DXB&limit=50
incidentsRouter.get('/', async (req, res) => {
  try {
    const { region, limit = 50 } = req.query;
    
    if (!region) {
      return res.status(400).json({ error: 'Region code required' });
    }
    
    const regionData = await db.getRegionByCode(region as string);
    if (!regionData) {
      return res.status(404).json({ error: 'Region not found' });
    }
    
    const incidents = await db.getIncidents(regionData.id, parseInt(limit as string));
    res.json({ 
      region: region,
      incidents,
      count: incidents.length
    });
  } catch (error) {
    console.error('[Incidents] Error:', error);
    res.status(500).json({ error: 'Failed to fetch incidents' });
  }
});

// GET /api/incidents/active?region=DXB
incidentsRouter.get('/active', async (req, res) => {
  try {
    const { region } = req.query;
    
    if (!region) {
      return res.status(400).json({ error: 'Region code required' });
    }
    
    const regionData = await db.getRegionByCode(region as string);
    if (!regionData) {
      return res.status(404).json({ error: 'Region not found' });
    }
    
    const incidents = await db.getActiveIncidents(regionData.id);
    res.json({ 
      region: region,
      incidents,
      count: incidents.length,
      hasActive: incidents.length > 0
    });
  } catch (error) {
    console.error('[Incidents] Error:', error);
    res.status(500).json({ error: 'Failed to fetch active incidents' });
  }
});
