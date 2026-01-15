#!/bin/bash
set -e
echo "========================================="
echo "VA-11 Intelligence Platform Deployment"
echo "========================================="

PROJECT_ID="va11-intelligence"
REGION="us-east4"
DB_INSTANCE="va11-db"
DB_NAME="va11_intelligence"
DB_USER="postgres"

gcloud config set project $PROJECT_ID
CLOUD_SQL_CONNECTION=$(gcloud sql instances describe $DB_INSTANCE --format='value(connectionName)')
echo "Cloud SQL: $CLOUD_SQL_CONNECTION"

echo ""
echo "Step 1: Deploy Bluesky Collector"
cd ../collectors
gcloud functions deploy bluesky-collector --gen2 --runtime=python311 --region=$REGION --source=. --entry-point=bluesky_collector_function --trigger-http --allow-unauthenticated --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER --set-secrets=BLUESKY_HANDLE=bluesky-handle:latest,BLUESKY_PASSWORD=bluesky-password:latest,DB_PASSWORD=db-password:latest --set-cloudsql-instances=$CLOUD_SQL_CONNECTION --timeout=540s --memory=512MB
echo "✓ Bluesky collector deployed!"
cd ..

echo ""
echo "Step 2: Deploy Sentiment Analyzer"
cd processors
gcloud functions deploy sentiment-analyzer --gen2 --runtime=python311 --region=$REGION --source=. --entry-point=sentiment_analyzer_function --trigger-http --allow-unauthenticated --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER --set-secrets=DB_PASSWORD=db-password:latest --set-cloudsql-instances=$CLOUD_SQL_CONNECTION --timeout=540s --memory=1024MB
echo "✓ Sentiment analyzer deployed!"
cd ..

echo ""
echo "Step 3: Set Up Scheduler"
BLUESKY_URL=$(gcloud functions describe bluesky-collector --region=$REGION --gen2 --format='value(serviceConfig.uri)')
SENTIMENT_URL=$(gcloud functions describe sentiment-analyzer --region=$REGION --gen2 --format='value(serviceConfig.uri)')

gcloud scheduler jobs create http bluesky-collection-job --location=$REGION --schedule="0 */6 * * *" --uri="$BLUESKY_URL" --http-method=POST --time-zone="America/New_York" 2>/dev/null || gcloud scheduler jobs update http bluesky-collection-job --location=$REGION --schedule="0 */6 * * *" --uri="$BLUESKY_URL"

gcloud scheduler jobs create http sentiment-analysis-job --location=$REGION --schedule="0 2,8,14,20 * * *" --uri="$SENTIMENT_URL" --http-method=POST --time-zone="America/New_York" 2>/dev/null || gcloud scheduler jobs update http sentiment-analysis-job --location=$REGION --schedule="0 2,8,14,20 * * *" --uri="$SENTIMENT_URL"

echo "✓ Scheduler created!"

echo ""
echo "Step 4: Deploy Dashboard"
cd dashboard
cat > Procfile << PROCFILEEOF
web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0
PROCFILEEOF

gcloud run deploy va11-dashboard --source=. --region=$REGION --platform=managed --allow-unauthenticated --set-env-vars=DB_NAME=$DB_NAME,DB_USER=$DB_USER --set-secrets=DB_PASSWORD=db-password:latest --set-cloudsql-instances=$CLOUD_SQL_CONNECTION --memory=1Gi

DASHBOARD_URL=$(gcloud run services describe va11-dashboard --region=$REGION --format='value(status.url)')
cd ..

echo ""
echo "========================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "========================================="
echo "Dashboard: $DASHBOARD_URL"
echo "Bluesky Collector: $BLUESKY_URL"
echo "Sentiment Analyzer: $SENTIMENT_URL"
echo ""
echo "Manually trigger first collection:"
echo "  curl -X POST $BLUESKY_URL"
echo "  curl -X POST $SENTIMENT_URL"
echo "========================================="
