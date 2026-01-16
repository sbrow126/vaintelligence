#!/bin/bash

PROJECT_ID="va11-intelligence"
REGION="us-east4"

echo "========================================="
echo "VA-11 Intelligence Platform"
echo "System Test Script"
echo "========================================="

gcloud config set project $PROJECT_ID

echo ""
echo "1. Testing Cloud Functions"
echo "========================================="

echo "Bluesky Collector:"
BLUESKY_RESULT=$(curl -s https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector)
echo $BLUESKY_RESULT | jq '.'

echo ""
echo "Reddit Collector:"
REDDIT_RESULT=$(curl -s https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector)
echo $REDDIT_RESULT | jq '.'

echo ""
echo "Sentiment Analyzer:"
SENTIMENT_RESULT=$(curl -s https://us-east4-va11-intelligence.cloudfunctions.net/sentiment-analyzer)
echo $SENTIMENT_RESULT | jq '.'

echo ""
echo "2. Testing Dashboard API"
echo "========================================="

echo "Stats Endpoint:"
curl -s https://va11-dashboard-466254020344.us-east4.run.app/api/stats | jq '.'

echo ""
echo "Timeseries Endpoint:"
curl -s https://va11-dashboard-466254020344.us-east4.run.app/api/timeseries?days=7 | jq '.' | head -20

echo ""
echo "3. Checking Cloud Scheduler"
echo "========================================="
gcloud scheduler jobs list --location=$REGION --format="table(name,state,schedule,lastAttemptTime)"

echo ""
echo "4. Database Status"
echo "========================================="
echo "Run this command to check database:"
echo "gcloud sql connect va11-db --user=postgres --database=va11_intelligence"
echo ""
echo "Then run:"
echo "SELECT platform, COUNT(*) as count, MAX(timestamp) as newest FROM social_media_posts GROUP BY platform;"

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
