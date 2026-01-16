#!/bin/bash

PROJECT_ID="va11-intelligence"
REGION="us-east4"
DB_NAME="va11_intelligence"
DB_USER="postgres"
CLOUD_SQL_CONNECTION="va11-intelligence:us-east4:va11-db"

echo "========================================="
echo "VA-11 Intelligence Platform"
echo "Complete Deployment Script"
echo "========================================="

gcloud config set project $PROJECT_ID

echo ""
echo "Step 1: Deploy Bluesky Collector"
echo "========================================="
cd ../collectors/bluesky
gcloud functions deploy bluesky-collector \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=bluesky_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --timeout=540s \
    --memory=512MB \
    --project=$PROJECT_ID

echo "✓ Bluesky collector deployed"

echo ""
echo "Step 2: Deploy Reddit Collector"
echo "========================================="
cd ../reddit
gcloud functions deploy reddit-collector \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=reddit_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --timeout=540s \
    --memory=512MB \
    --project=$PROJECT_ID

echo "✓ Reddit collector deployed"

echo ""
echo "Step 3: Deploy Sentiment Analyzer"
echo "========================================="
cd ../../processors/sentiment
gcloud functions deploy sentiment-analyzer \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=sentiment_analyzer_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION \
    --set-secrets=DB_PASSWORD=db-password:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --timeout=540s \
    --memory=1024MB \
    --project=$PROJECT_ID

echo "✓ Sentiment analyzer deployed"

echo ""
echo "Step 4: Setup Cloud Scheduler"
echo "========================================="

gcloud scheduler jobs delete bluesky-collector-schedule --location=$REGION --quiet 2>/dev/null
gcloud scheduler jobs delete reddit-collector-schedule --location=$REGION --quiet 2>/dev/null
gcloud scheduler jobs delete sentiment-analyzer-schedule --location=$REGION --quiet 2>/dev/null

gcloud scheduler jobs create http bluesky-collector-schedule \
    --location=$REGION \
    --schedule="0 */6 * * *" \
    --uri="https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector" \
    --http-method=GET \
    --project=$PROJECT_ID

gcloud scheduler jobs create http reddit-collector-schedule \
    --location=$REGION \
    --schedule="0 */6 * * *" \
    --uri="https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector" \
    --http-method=GET \
    --project=$PROJECT_ID

gcloud scheduler jobs create http sentiment-analyzer-schedule \
    --location=$REGION \
    --schedule="0 * * * *" \
    --uri="https://us-east4-va11-intelligence.cloudfunctions.net/sentiment-analyzer" \
    --http-method=GET \
    --project=$PROJECT_ID

echo "✓ Schedulers created"

echo ""
echo "Step 5: Deploy Dashboard"
echo "========================================="
cd ../../dashboard

gcloud run deploy va11-dashboard \
    --source . \
    --platform managed \
    --region=$REGION \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_CONNECTION,GCP_PROJECT=$PROJECT_ID \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --add-cloudsql-instances=$CLOUD_SQL_CONNECTION \
    --project=$PROJECT_ID

echo "✓ Dashboard deployed"

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Dashboard URL:"
echo "https://va11-dashboard-466254020344.us-east4.run.app"
echo ""
echo "Testing collectors..."
echo ""

curl -s https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector | jq '.'
curl -s https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector | jq '.'

echo ""
echo "Wait 5 minutes, then check database:"
echo "gcloud sql connect va11-db --user=postgres --database=va11_intelligence"
echo "SELECT platform, COUNT(*) FROM social_media_posts GROUP BY platform;"
