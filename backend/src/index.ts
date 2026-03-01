import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';

import { db } from './services/database';
import { regionsRouter } from './routes/regions';
import { incidentsRouter } from './routes/incidents';
import { sourcesRouter } from './routes/sources';
import { alertsRouter } from './routes/alerts';
import { startIngestion } from './ingestion/scheduler';

dotenv.config();

const app = express();
const server = createServer(app);
const wss = new WebSocketServer({ server });

const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Health check
app.get('/health', async (req, res) => {
  const dbHealthy = await db.healthCheck();
  res.json({
    status: dbHealthy ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    version: '0.1.0'
  });
});

// API Routes
app.use('/api/regions', regionsRouter);
app.use('/api/incidents', incidentsRouter);
app.use('/api/sources', sourcesRouter);
app.use('/api/alerts', alertsRouter);

// WebSocket for real-time alerts
const clients = new Map<string, WebSocket>();

wss.on('connection', (ws, req) => {
  const clientId = Math.random().toString(36).substring(7);
  clients.set(clientId, ws);
  
  console.log(`[WS] Client connected: ${clientId}`);
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());
      
      // Subscribe to region updates
      if (data.type === 'subscribe' && data.regionId) {
        (ws as any).regionId = data.regionId;
        ws.send(JSON.stringify({ type: 'subscribed', regionId: data.regionId }));
      }
    } catch (err) {
      console.error('[WS] Invalid message:', err);
    }
  });
  
  ws.on('close', () => {
    clients.delete(clientId);
    console.log(`[WS] Client disconnected: ${clientId}`);
  });
  
  // Send initial connection success
  ws.send(JSON.stringify({ type: 'connected', clientId }));
});

// Broadcast to region subscribers
export function broadcastToRegion(regionId: string, data: any) {
  clients.forEach((ws) => {
    if ((ws as any).regionId === regionId && ws.readyState === 1) {
      ws.send(JSON.stringify(data));
    }
  });
}

// Start ingestion services
startIngestion();

server.listen(PORT, () => {
  console.log(`[Gulf Watch] Server running on port ${PORT}`);
  console.log(`[Gulf Watch] Environment: ${process.env.NODE_ENV || 'development'}`);
});

export { app, wss };
