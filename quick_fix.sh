#!/bin/bash

echo "========================================="
echo "VA-11 Intelligence - Quick Fix Script"
echo "========================================="
echo ""
echo "This will:"
echo "1. Check current collector status"
echo "2. Manually trigger all collectors for backfill"
echo "3. Verify data is being collected"
echo "4. Check scheduler status"
echo ""

PROJECT_ID="va11-intelligence"
REGION="us-east4"

gcloud config set project $PROJECT_ID

echo "Step 1: Current Collector Status"
echo "========================================="
echo "Deployed functions:"
gcloud functions list --gen2 --region=$REGION --format="table(name,state,updateTime)"

echo ""
echo "Cloud Scheduler jobs:"
gcloud scheduler jobs list --location=$REGION --format="table(name,state,schedule,lastAttemptTime)"

echo ""
echo "Step 2: Check Database Current State"
echo "========================================="
echo "Connecting to database to check post counts..."

# You'll need to run this part manually in Cloud Shell
echo "Run this command to see current data:"
echo "gcloud sql connect va11-db --user=postgres --database=va11_intelligence"
echo "Then run:"
echo "SELECT platform, COUNT(*) as count, MIN(timestamp) as oldest, MAX(timestamp) as newest FROM social_media_posts GROUP BY platform;"

echo ""
echo "Step 3: Manually Trigger All Collectors"
echo "========================================="

read -p "Trigger Bluesky collector now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Triggering Bluesky collector..."
    curl -X POST -w "\nStatus: %{http_code}\n" https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector
    echo ""
fi

read -p "Trigger Mastodon collector now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Triggering Mastodon collector..."
    curl -X POST -w "\nStatus: %{http_code}\n" https://us-east4-va11-intelligence.cloudfunctions.net/mastodon-collector
    echo ""
fi

read -p "Trigger YouTube collector now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Triggering YouTube collector..."
    curl -X POST -w "\nStatus: %{http_code}\n" https://us-east4-va11-intelligence.cloudfunctions.net/youtube-collector
    echo ""
fi

read -p "Trigger Reddit collector now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Triggering Reddit collector..."
    curl -X POST -w "\nStatus: %{http_code}\n" https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector
    echo ""
fi

echo ""
echo "Step 4: Check Scheduler Jobs Are Enabled"
echo "========================================="

SCHEDULERS=("bluesky-collector-schedule" "mastodon-collector-schedule" "youtube-collector-schedule" "reddit-collector-schedule" "sentiment-analyzer-schedule")

for SCHEDULER in "${SCHEDULERS[@]}"; do
    STATUS=$(gcloud scheduler jobs describe $SCHEDULER --location=$REGION --format="value(state)" 2>/dev/null)
    if [ "$STATUS" == "ENABLED" ]; then
        echo "✓ $SCHEDULER is ENABLED"
    elif [ "$STATUS" == "PAUSED" ]; then
        echo "✗ $SCHEDULER is PAUSED - resuming..."
        gcloud scheduler jobs resume $SCHEDULER --location=$REGION
    else
        echo "? $SCHEDULER not found or error"
    fi
done

echo ""
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo "1. Wait 5-10 minutes for collectors to finish"
echo "2. Check database again for new posts"
echo "3. Refresh dashboard to see updated data"
echo "4. Monitor logs: gcloud functions logs read bluesky-collector --region=$REGION --limit=50"
echo ""
echo "Expected result: 200-500 total posts across all platforms from last 7 days"
echo "========================================="
