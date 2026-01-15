# Cloud Functions Deployment Guide

## Prerequisites
1. GCP Project created
2. Cloud SQL PostgreSQL instance running
3. Cloud Functions API enabled
4. Cloud Scheduler API enabled
5. Service account with appropriate permissions

## Deploy Functions

### 1. Deploy Reddit Collector
```bash
gcloud functions deploy reddit-collector \
  --runtime python311 \
  --trigger-http \
  --entry-point reddit_collector_function \
  --source collectors/ \
  --set-env-vars DB_HOST=$DB_HOST,DB_NAME=$DB_NAME,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD \
  --set-secrets REDDIT_CLIENT_ID=reddit-client-id:latest,REDDIT_CLIENT_SECRET=reddit-client-secret:latest \
  --timeout 540s \
  --memory 512MB \
  --region us-east4
```

### 2. Deploy Bluesky Collector
```bash
gcloud functions deploy bluesky-collector \
  --runtime python311 \
  --trigger-http \
  --entry-point bluesky_collector_function \
  --source collectors/ \
  --set-env-vars DB_HOST=$DB_HOST,DB_NAME=$DB_NAME,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD \
  --set-secrets BLUESKY_HANDLE=bluesky-handle:latest,BLUESKY_PASSWORD=bluesky-password:latest \
  --timeout 540s \
  --memory 512MB \
  --region us-east4
```

### 3. Deploy Sentiment Analyzer
```bash
gcloud functions deploy sentiment-analyzer \
  --runtime python311 \
  --trigger-http \
  --entry-point sentiment_analyzer_function \
  --source processors/ \
  --set-env-vars DB_HOST=$DB_HOST,DB_NAME=$DB_NAME,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD \
  --timeout 540s \
  --memory 1024MB \
  --region us-east4
```

## Set Up Cloud Scheduler Jobs

### Reddit Collection (Every 6 hours)
```bash
gcloud scheduler jobs create http reddit-collection-job \
  --schedule="0 */6 * * *" \
  --uri="https://us-east4-YOUR_PROJECT_ID.cloudfunctions.net/reddit-collector" \
  --http-method=POST \
  --location=us-east4 \
  --time-zone="America/New_York"
```

### Bluesky Collection (Every 6 hours, offset by 1 hour)
```bash
gcloud scheduler jobs create http bluesky-collection-job \
  --schedule="0 1,7,13,19 * * *" \
  --uri="https://us-east4-YOUR_PROJECT_ID.cloudfunctions.net/bluesky-collector" \
  --http-method=POST \
  --location=us-east4 \
  --time-zone="America/New_York"
```

### Sentiment Analysis (Every 6 hours, offset by 2 hours)
```bash
gcloud scheduler jobs create http sentiment-analysis-job \
  --schedule="0 2,8,14,20 * * *" \
  --uri="https://us-east4-YOUR_PROJECT_ID.cloudfunctions.net/sentiment-analyzer" \
  --http-method=POST \
  --location=us-east4 \
  --time-zone="America/New_York"
```

## Store Secrets in Secret Manager

```bash
# Reddit credentials
echo -n "your-reddit-client-id" | gcloud secrets create reddit-client-id --data-file=-
echo -n "your-reddit-client-secret" | gcloud secrets create reddit-client-secret --data-file=-

# Bluesky credentials
echo -n "your.handle.bsky.social" | gcloud secrets create bluesky-handle --data-file=-
echo -n "your-app-password" | gcloud secrets create bluesky-password --data-file=-
```

## Initialize Database

```bash
# Run locally first to create tables
python database/models.py
```

## Test Functions Manually

```bash
# Test Reddit collector
curl -X POST https://us-east4-YOUR_PROJECT_ID.cloudfunctions.net/reddit-collector

# Test Bluesky collector
curl -X POST https://us-east4-YOUR_PROJECT_ID.cloudfunctions.net/bluesky-collector

# Test sentiment analyzer
curl -X POST https://us-east4-YOUR_PROJECT_ID.cloudfunctions.net/sentiment-analyzer
```

## Monitoring

View logs:
```bash
gcloud functions logs read reddit-collector --region=us-east4
gcloud functions logs read bluesky-collector --region=us-east4
gcloud functions logs read sentiment-analyzer --region=us-east4
```

## Estimated Costs
- Cloud Functions: ~$5-10/month (generous free tier)
- Cloud SQL (db-f1-micro): ~$15-20/month
- Cloud Scheduler: ~$0.10/month
- Natural Language API: ~$10-30/month (depends on volume)
- **Total: ~$30-60/month**
