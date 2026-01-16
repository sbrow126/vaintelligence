# Complete Deployment Guide

## System Overview

VA-11 Intelligence Platform monitors social media for constituent sentiment in Virginia's 11th district.

### Architecture

```
Google Cloud Platform
├── Cloud Functions
│   ├── bluesky-collector (every 6 hours)
│   ├── reddit-collector (every 6 hours)
│   └── sentiment-analyzer (every hour)
├── Cloud SQL (PostgreSQL 15)
│   └── va11_intelligence database
├── Cloud Run
│   └── Flask dashboard
└── Cloud Scheduler
    └── Automated triggers
```

## Prerequisites

### Required
- Google Cloud project: va11-intelligence
- Billing enabled
- APIs enabled:
  - Cloud Functions API
  - Cloud Run API
  - Cloud SQL Admin API
  - Cloud Scheduler API
  - Secret Manager API

### Existing Resources
- Cloud SQL instance: va11-db
- Database: va11_intelligence
- Connection: va11-intelligence:us-east4:va11-db

## Deployment Steps

### 1. Prepare Secrets

Ensure these secrets exist in Secret Manager:

```bash
gcloud secrets versions access latest --secret=db-password
gcloud secrets versions access latest --secret=anthropic-api-key
```

If missing, create them:

```bash
echo -n "SecureVA11Pass2024!" | gcloud secrets create db-password --data-file=-
echo -n "YOUR_ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=-
```

### 2. Deploy Collectors

```bash
cd deployment
chmod +x deploy_all.sh
./deploy_all.sh
```

Or deploy individually:

```bash
cd collectors/bluesky
gcloud functions deploy bluesky-collector \
    --gen2 \
    --runtime=python311 \
    --region=us-east4 \
    --source=. \
    --entry-point=bluesky_collector_function \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=va11_intelligence,DB_USER=postgres,CLOUD_SQL_CONNECTION_NAME=va11-intelligence:us-east4:va11-db \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --timeout=540s \
    --memory=512MB
```

### 3. Setup Automation

Cloud Scheduler jobs run collectors automatically:

```bash
gcloud scheduler jobs create http bluesky-collector-schedule \
    --location=us-east4 \
    --schedule="0 */6 * * *" \
    --uri="https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector" \
    --http-method=GET
```

### 4. Deploy Dashboard

```bash
cd dashboard

gcloud run deploy va11-dashboard \
    --source . \
    --platform managed \
    --region=us-east4 \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=va11_intelligence,DB_USER=postgres,CLOUD_SQL_CONNECTION_NAME=va11-intelligence:us-east4:va11-db \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --add-cloudsql-instances=va11-intelligence:us-east4:va11-db
```

### 5. Verify Deployment

Test collectors:

```bash
curl https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector
curl https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector
curl https://us-east4-va11-intelligence.cloudfunctions.net/sentiment-analyzer
```

Check database:

```bash
gcloud sql connect va11-db --user=postgres --database=va11_intelligence

SELECT platform, COUNT(*) FROM social_media_posts GROUP BY platform;
```

## Monitoring

### View Logs

```bash
gcloud functions logs read bluesky-collector --region=us-east4 --limit=50
gcloud run services logs read va11-dashboard --region=us-east4 --limit=50
```

### Check Scheduler Status

```bash
gcloud scheduler jobs list --location=us-east4
```

### Monitor Database

```sql
SELECT 
    DATE(timestamp) as date,
    platform,
    COUNT(*) as posts
FROM social_media_posts
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp), platform
ORDER BY date DESC, posts DESC;
```

## Troubleshooting

### Collectors Return 0 Posts

Check logs for errors:
```bash
gcloud functions logs read bluesky-collector --region=us-east4 --limit=30
```

Common issues:
- Database connection failed
- API rate limits
- Search terms not matching

### Dashboard Shows No Data

1. Verify data exists:
```bash
gcloud sql connect va11-db --user=postgres --database=va11_intelligence
SELECT COUNT(*) FROM social_media_posts;
```

2. Check dashboard logs:
```bash
gcloud run services logs read va11-dashboard --region=us-east4 --limit=50
```

3. Test API endpoints:
```bash
curl https://va11-dashboard-466254020344.us-east4.run.app/api/stats
```

### Sentiment Analysis Not Running

Check if posts are marked as processed:
```sql
SELECT processed, COUNT(*) 
FROM social_media_posts 
GROUP BY processed;
```

Manually trigger analyzer:
```bash
curl https://us-east4-va11-intelligence.cloudfunctions.net/sentiment-analyzer
```

## Maintenance

### Update Collectors

1. Modify code in `collectors/` directory
2. Redeploy:
```bash
cd collectors/bluesky
gcloud functions deploy bluesky-collector --source . --region=us-east4
```

### Update Dashboard

1. Modify code in `dashboard/` directory
2. Redeploy:
```bash
cd dashboard
gcloud run deploy va11-dashboard --source . --region=us-east4
```

### Database Maintenance

Archive old data (optional):
```sql
DELETE FROM social_media_posts WHERE timestamp < NOW() - INTERVAL '90 days';
VACUUM ANALYZE;
```

## Cost Management

### Current Costs (~$10-15/month)

- Cloud SQL: $7-10 (db-f1-micro)
- Cloud Run: $5 (includes free tier)
- Cloud Functions: FREE (under 2M invocations)
- Cloud Scheduler: FREE (under 3 jobs)
- Anthropic API: $2-5 (based on volume)

### Reduce Costs

1. Decrease collector frequency:
```bash
gcloud scheduler jobs update http bluesky-collector-schedule \
    --schedule="0 */12 * * *"
```

2. Implement data retention:
```sql
DELETE FROM social_media_posts WHERE timestamp < NOW() - INTERVAL '60 days';
```

3. Use smaller Cloud SQL instance:
```bash
gcloud sql instances patch va11-db --tier=db-f1-micro
```

## Security

### Access Control

Dashboard is public (no sensitive data). To add authentication:

```bash
gcloud run services update va11-dashboard \
    --region=us-east4 \
    --no-allow-unauthenticated
```

### Secret Rotation

Rotate database password:
```bash
echo -n "NEW_PASSWORD" | gcloud secrets versions add db-password --data-file=-

gcloud functions deploy bluesky-collector \
    --update-secrets=DB_PASSWORD=db-password:latest
```

### Audit Logging

Enable audit logs:
```bash
gcloud logging read "resource.type=cloud_function" --limit=100
```

## Scaling

### Increase Data Collection

Add more search terms in `collectors/bluesky/main.py`:
```python
search_terms = [
    "Reston Virginia",
    "Fairfax County",
    "ADD MORE TERMS HERE"
]
```

### Add Data Sources

1. Create new collector in `collectors/`
2. Deploy as Cloud Function
3. Add to Cloud Scheduler
4. Update dashboard queries

### Handle High Traffic

Increase Cloud Run instances:
```bash
gcloud run services update va11-dashboard \
    --region=us-east4 \
    --max-instances=10 \
    --min-instances=1
```

## Support

- GitHub: https://github.com/sbrow126/va11-intelligence-platform
- Issues: https://github.com/sbrow126/va11-intelligence-platform/issues
- Contact: Dr. Shallon Elizabeth Brown
- Email: contact@ctoadvisorpro.com
