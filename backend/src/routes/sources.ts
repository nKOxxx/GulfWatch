import { Router } from 'express';
import { db } from '../services/database';

export const sourcesRouter = Router();

// GET /api/sources/partnerships - List camera partnerships
sourcesRouter.get('/partnerships', async (req, res) => {
  try {
    const partnerships = await db.getPartnerships();
    res.json({ partnerships });
  } catch (error) {
    console.error('[Sources] Error:', error);
    res.status(500).json({ error: 'Failed to fetch partnerships' });
  }
});

// POST /api/sources/partnerships - Register new partnership
sourcesRouter.post('/partnerships', async (req, res) => {
  try {
    const { organizationName, organizationType, contactEmail, cameraCount, regions } = req.body;
    
    if (!organizationName || !contactEmail) {
      return res.status(400).json({ error: 'Organization name and contact email required' });
    }
    
    const partnership = await db.createPartnership({
      organizationName,
      organizationType: organizationType || 'private',
      contactEmail,
      cameraCount: cameraCount || 0,
      regions: regions || []
    });
    
    res.status(201).json({ partnership });
  } catch (error) {
    console.error('[Sources] Error:', error);
    res.status(500).json({ error: 'Failed to create partnership' });
  }
});
