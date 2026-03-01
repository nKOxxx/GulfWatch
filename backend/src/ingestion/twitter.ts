import axios from 'axios';
import { db } from '../services/database';

// Keywords for threat detection
const THREAT_KEYWORDS = [
  'explosion', 'blast', 'boom', 'loud noise',
  'drone', 'uav', 'missile', 'rocket',
  'siren', 'air raid', 'civil defense',
  'attack', 'strike', 'impact',
  'انفجار', 'طائرة مسيرة', 'صاروخ', 'إنذار'
];

export class TwitterIngester {
  private bearerToken: string;
  private baseUrl = 'https://api.twitter.com/2';
  
  constructor() {
    this.bearerToken = process.env.TWITTER_BEARER_TOKEN || '';
  }
  
  async poll() {
    // Get active regions
    const regions = await db.getRegions();
    
    for (const region of regions) {
      await this.searchRegion(region);
    }
  }
  
  private async searchRegion(region: any) {
    try {
      // Build query: keywords + geofence
      const query = `(${THREAT_KEYWORDS.join(' OR ')}) -is:retweet has:geo`;
      
      // Note: Full geo search requires Twitter API v2 with academic/elevated access
      // This is a simplified version
      const response = await axios.get(
        `${this.baseUrl}/tweets/search/recent`,
        {
          headers: {
            Authorization: `Bearer ${this.bearerToken}`
          },
          params: {
            query: query,
            max_results: 10,
            'tweet.fields': 'created_at,geo,author_id,attachments',
            'expansions': 'author_id',
            'user.fields': 'location'
          }
        }
      );
      
      if (!response.data.data) return;
      
      for (const tweet of response.data.data) {
        await this.processTweet(tweet, region);
      }
      
    } catch (error: any) {
      if (error.response?.status === 429) {
        console.log('[Twitter] Rate limited, will retry');
      } else {
        console.error('[Twitter] Search error:', error.message);
      }
    }
  }
  
  private async processTweet(tweet: any, region: any) {
    try {
      // Skip if no geo data
      if (!tweet.geo?.coordinates) {
        // Try to extract location from text or user profile
        // For now, skip
        return;
      }
      
      const [lng, lat] = tweet.geo.coordinates.coordinates;
      
      // Detect event type from text
      const text = tweet.text.toLowerCase();
      let eventType = 'unknown';
      
      if (text.includes('explosion') || text.includes('blast') || text.includes('انفجار')) {
        eventType = 'explosion';
      } else if (text.includes('drone') || text.includes('uav') || text.includes('مسيرة')) {
        eventType = 'drone_sighting';
      } else if (text.includes('siren') || text.includes('إنذار')) {
        eventType = 'siren';
      } else if (text.includes('missile') || text.includes('rocket') || text.includes('صاروخ')) {
        eventType = 'missile';
      }
      
      // Create raw event
      await db.createRawEvent({
        sourceId: 'twitter-api', // Would lookup actual source_id from DB
        regionId: region.id,
        eventType,
        location: { lat, lng },
        detectedAt: new Date(tweet.created_at),
        rawData: tweet,
        textContent: tweet.text,
        mediaUrls: tweet.attachments?.media_keys || []
      });
      
      console.log(`[Twitter] New event: ${eventType} in ${region.name}`);
      
    } catch (error) {
      console.error('[Twitter] Processing error:', error);
    }
  }
}
