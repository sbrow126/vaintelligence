# VA-11 Intelligence Platform - Collector Fix Guide

## Current Issues Identified

1. ❌ Only Bluesky data is being collected
2. ❌ No data collected since 1/15/2026
3. ❌ Mastodon, YouTube, Reddit collectors not working
4. ❌ Need 7-day backfill to build initial dataset
5. ❌ Data pool needs to grow continuously

## Solution: Complete Collector Rebuild

### Step 1: Check Current State

Run this in Google Cloud Shell:

```bash
# Check what's deployed
gcloud functions list --gen2 --region=us-east4 --project=va11-intelligence

# Check schedulers
gcloud scheduler jobs list --location=us-east4 --project=va11-intelligence

# Check database
gcloud sql connect va11-db --user=postgres --database=va11_intelligence << 'EOF'
SELECT platform, COUNT(*) as count, MIN(timestamp) as oldest, MAX(timestamp) as newest 
FROM social_media_posts 
GROUP BY platform;
EOF
```

### Step 2: Fix Bluesky Collector (Add 7-Day Backfill)

The Bluesky collector needs to:
- Collect last 7 days of data on first run
- Then switch to incremental (6-hour windows)
- Store a "last_run" timestamp

```bash
cd ~/vaintelligence/collectors/bluesky

# Update main.py to add backfill logic
# Key changes needed:
# 1. Check for BACKFILL_DAYS environment variable
# 2. If set, collect that many days of history
# 3. Store last collection timestamp in database
# 4. On subsequent runs, only collect since last timestamp
```

### Step 3: Deploy/Fix All Collectors

```bash
# Set variables
PROJECT_ID="va11-intelligence"
REGION="us-east4"
DB_NAME="va11_intelligence"
DB_USER="postgres"
CLOUD_SQL_CONNECTION="va11-intelligence:us-east4:va11-db"

gcloud config set project $PROJECT_ID

# Deploy Bluesky with 7-day backfill
cd ~/vaintelligence/collectors/bluesky
gcloud functions deploy bluesky-collector \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=bluesky_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,BACKFILL_DAYS=7 \
    --set-secrets=BLUESKY_HANDLE=bluesky-handle:latest,BLUESKY_PASSWORD=bluesky-password:latest,DB_PASSWORD=db-password:latest \
    --timeout=540s \
    --memory=512MB \
    --project=$PROJECT_ID

# Deploy Mastodon (if not working)
cd ~/vaintelligence/collectors/mastodon
gcloud functions deploy mastodon-collector \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=mastodon_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,BACKFILL_DAYS=7 \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --timeout=540s \
    --memory=512MB \
    --project=$PROJECT_ID

# Deploy YouTube
cd ~/vaintelligence/collectors/youtube
gcloud functions deploy youtube-collector \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=youtube_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,BACKFILL_DAYS=7 \
    --set-secrets=DB_PASSWORD=db-password:latest,YOUTUBE_API_KEY=youtube-api-key:latest \
    --timeout=540s \
    --memory=512MB \
    --project=$PROJECT_ID

# Deploy Reddit
cd ~/vaintelligence/collectors/reddit
gcloud functions deploy reddit-collector \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=reddit_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,BACKFILL_DAYS=7 \
    --set-secrets=DB_PASSWORD=db-password:latest,REDDIT_CLIENT_ID=reddit-client-id:latest,REDDIT_CLIENT_SECRET=reddit-client-secret:latest \
    --timeout=540s \
    --memory=512MB \
    --project=$PROJECT_ID
```

### Step 4: Manually Trigger Backfill

```bash
echo "Triggering 7-day backfill for all collectors..."

# Bluesky
echo "Bluesky..."
curl -X POST https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector

# Wait between calls to avoid rate limits
sleep 30

# Mastodon
echo "Mastodon..."
curl -X POST https://us-east4-va11-intelligence.cloudfunctions.net/mastodon-collector

sleep 30

# YouTube
echo "YouTube..."
curl -X POST https://us-east4-va11-intelligence.cloudfunctions.net/youtube-collector

sleep 30

# Reddit
echo "Reddit..."
curl -X POST https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector

echo "Backfill triggered! Wait 5-10 minutes then check database."
```

### Step 5: Update Environment Variables (Remove Backfill Mode)

After initial backfill completes, update collectors to incremental mode:

```bash
# Remove BACKFILL_DAYS variable so they collect incrementally
for COLLECTOR in bluesky-collector mastodon-collector youtube-collector reddit-collector; do
    gcloud functions deploy $COLLECTOR \
        --gen2 \
        --region=$REGION \
        --update-env-vars=BACKFILL_DAYS=0 \
        --project=$PROJECT_ID
done
```

### Step 6: Verify Schedulers Are Running

```bash
# List all scheduler jobs
gcloud scheduler jobs list --location=$REGION --project=$PROJECT_ID

# Verify they're ENABLED
# If any show PAUSED, resume them:
gcloud scheduler jobs resume bluesky-collector-schedule --location=$REGION
gcloud scheduler jobs resume mastodon-collector-schedule --location=$REGION
gcloud scheduler jobs resume youtube-collector-schedule --location=$REGION
gcloud scheduler jobs resume reddit-collector-schedule --location=$REGION
```

### Step 7: Verify Data is Growing

```bash
# Check post counts
gcloud sql connect va11-db --user=postgres --database=va11_intelligence << 'EOF'
-- Total posts by platform
SELECT platform, COUNT(*) as count, MAX(timestamp) as latest
FROM social_media_posts
GROUP BY platform
ORDER BY count DESC;

-- Posts per day
SELECT DATE(timestamp) as date, COUNT(*) as posts
FROM social_media_posts
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 10;
EOF
```

## Expected Results After Fix

After completing all steps, you should see:

✅ **~200-500 posts** from last 7 days across all platforms
✅ **Bluesky**: 50-100 posts  
✅ **Mastodon**: 20-50 posts  
✅ **YouTube**: 30-80 posts (comments on local news videos)  
✅ **Reddit**: 100-300 posts (r/nova, r/fairfaxcounty, r/reston)  

✅ **New posts every 6 hours** as schedulers run
✅ **Data pool continuously growing**

## Troubleshooting

### If a collector returns 0 posts:

**Bluesky**: Check search terms, ensure @repwalkinshaw.bsky.social exists
**Mastodon**: Expand search terms, check mastodon.social API access
**YouTube**: Verify YouTube API key is valid, check quota limits
**Reddit**: Verify Reddit API credentials, check rate limits

### If schedulers aren't running:

```bash
# Check scheduler job status
gcloud scheduler jobs describe bluesky-collector-schedule --location=$REGION

# Check last run time and result
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=bluesky-collector-schedule" --limit=10
```

### If data stops growing:

1. Check Cloud Scheduler is enabled
2. Verify collectors aren't hitting rate limits
3. Check Cloud Functions logs for errors
4. Verify database connections aren't timing out

## Monitoring Setup

Add this to get alerts when data stops flowing:

```bash
# Create alert policy
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="VA-11 Data Collection Alert" \
    --condition-display-name="No new posts in 12 hours" \
    --condition-threshold-value=1 \
    --condition-threshold-duration=43200s
```

---

**Next Steps**: Run Step 1 to check current state, then follow steps 2-7 to fix all collectors.
