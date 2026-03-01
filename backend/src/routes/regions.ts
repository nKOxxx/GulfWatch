import { Router } from 'express';
import { db } from '../services/database';

export const regionsRouter = Router();

// GET /api/regions - List all regions
regionsRouter.get('/', async (req, res) => {
  try {
    const regions = await db.getRegions();
    res.json({ regions });
  } catch (error) {
    console.error('[Regions] Error:', error);
    res.status(500).json({ error: 'Failed to fetch regions' });
  }
});

// GET /api/regions/:code - Get specific region
regionsRouter.get('/:code', async (req, res) => {
  try {
    const region = await db.getRegionByCode(req.params.code);
    if (!region) {
      return res.status(404).json({ error: 'Region not found' });
    }
    res.json({ region });
  } catch (error) {
    console.error('[Regions] Error:', error);
    res.status(500).json({ error: 'Failed to fetch region' });
  }
});

// GET /api/regions/:code/sources - Get data sources for region
regionsRouter.get('/:code/sources', async (req, res) => {
  try {
    const region = await db.getRegionByCode(req.params.code);
    if (!region) {
      return res.status(404).json({ error: 'Region not found' });
    }
    const sources = await db.getSourcesByRegion(region.id);
    res.json({ sources });
  } catch (error) {
    console.error('[Regions] Error:', error);
    res.status(500).json({ error: 'Failed to fetch sources' });
  }
});
