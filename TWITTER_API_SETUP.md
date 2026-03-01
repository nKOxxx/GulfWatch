# Twitter API Setup for Gulf Watch

## Step 1: Get Twitter API Access

1. Go to https://developer.twitter.com
2. Sign in with your Twitter account
3. Apply for Developer Account (free tier available)
4. Create a new Project → App
5. Generate "Bearer Token"

## Step 2: Add to Render Environment Variables

On Render Dashboard:
```
1. Go to your gulf-watch-api service
2. Click "Environment" tab
3. Add Variable:
   - Key: TWITTER_BEARER_TOKEN
   - Value: [paste your bearer token]
4. Click "Save Changes"
5. Service will auto-restart
```

## Step 3: Test Ingestion

Visit:
```
https://gulf-watch-api.onrender.com/admin/ingest-twitter
```

Should return:
```json
{
  "status": "success",
  "new_reports": 5,
  "auto_verified": 3,
  "message": "Ingested 5 reports, auto-verified 3 incidents"
}
```

## Step 4: Create Demo Data (Optional)

If you don't have Twitter API yet, create demo incidents:
```
https://gulf-watch-api.onrender.com/admin/demo-incidents
```

This creates fake incidents to test the UI.

## Monitored Sources

Twitter ingestion monitors these official UAE accounts:
- @WAMnews (WAM News)
- @uae_cd (Civil Defense)
- @moiuae (Ministry of Interior)
- @ncema_uae (Emergency Management)
- @dubaipolicehq (Dubai Police)
- @mohamedbinzayed (President)
- @hhshkmohd (Dubai Ruler)

## Auto-Verification

Reports from official sources (@uae_cd, @moiuae, etc.) are automatically marked as "CONFIRMED" without requiring cross-verification.

Reports from other sources require multiple sources to confirm.

## Running Ingestion

### Manual (one-time):
```
POST https://gulf-watch-api.onrender.com/admin/ingest-twitter
```

### Automatic (coming soon):
- Every 30 seconds via cron job
- Webhook on new tweets
- WebSocket push to frontend
