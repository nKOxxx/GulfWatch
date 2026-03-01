import { Router } from 'express';
import { broadcastToRegion } from '../index';

export const alertsRouter = Router();

// POST /api/alerts/broadcast - Broadcast alert to region (admin only)
alertsRouter.post('/broadcast', async (req, res) => {
  try {
    // TODO: Add authentication middleware
    const { regionId, severity, title, message, channels } = req.body;
    
    if (!regionId || !title || !message) {
      return res.status(400).json({ error: 'Region, title, and message required' });
    }
    
    // Broadcast via WebSocket
    broadcastToRegion(regionId, {
      type: 'alert',
      severity: severity || 'medium',
      title,
      message,
      timestamp: new Date().toISOString()
    });
    
    res.json({ 
      success: true, 
      message: 'Alert broadcast initiated',
      regionId,
      channels: channels || ['websocket']
    });
  } catch (error) {
    console.error('[Alerts] Error:', error);
    res.status(500).json({ error: 'Failed to broadcast alert' });
  }
});
