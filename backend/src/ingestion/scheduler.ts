import cron from 'node-cron';
import { TwitterIngester } from './twitter';

let isRunning = false;

export function startIngestion() {
  if (isRunning) return;
  isRunning = true;
  
  console.log('[Ingestion] Starting data ingestion services...');
  
  // Twitter ingestion - every 30 seconds
  if (process.env.TWITTER_BEARER_TOKEN) {
    const twitterIngester = new TwitterIngester();
    cron.schedule('*/30 * * * * *', async () => {
      try {
        await twitterIngester.poll();
      } catch (error) {
        console.error('[Ingestion] Twitter error:', error);
      }
    });
    console.log('[Ingestion] Twitter ingester scheduled');
  } else {
    console.log('[Ingestion] Twitter ingester skipped (no bearer token)');
  }
  
  // Future: Telegram, news feeds, ADS-B, camera streams
  
  console.log('[Ingestion] All services started');
}
