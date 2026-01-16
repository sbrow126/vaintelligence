# Quick Start Guide

Get VA-11 Intelligence Platform running in 15 minutes.

## Prerequisites

- Google Cloud account
- GitHub account (sbrow126)
- Cloud Shell access

## Step 1: Upload to GitHub (5 minutes)

```bash
cd ~
tar -xzf va11-intelligence-platform.tar.gz
cd va11-intelligence-platform

git init
git add .
git commit -m "VA-11 Intelligence Platform - Complete deployment"
git remote add origin https://github.com/sbrow126/va11-intelligence-platform.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Google Cloud (10 minutes)

```bash
cd deployment
chmod +x deploy_all.sh
./deploy_all.sh
```

This deploys:
- Bluesky collector
- Reddit collector  
- Sentiment analyzer
- Cloud Scheduler jobs
- Dashboard

## Step 3: Verify (2 minutes)

Open dashboard:
```
https://va11-dashboard-466254020344.us-east4.run.app
```

Check database:
```bash
gcloud sql connect va11-db --user=postgres --database=va11_intelligence --quiet
```

Password: `SecureVA11Pass2024!`

```sql
SELECT platform, COUNT(*) as count, MAX(timestamp) as newest 
FROM social_media_posts 
GROUP BY platform 
ORDER BY count DESC;
```

## Expected Results

After first deployment:
- Bluesky: 50-100 posts
- Reddit: 100-200 posts
- Total: 150-300 posts

After 24 hours:
- Bluesky: 200+ posts
- Reddit: 500+ posts  
- Total: 700+ posts

## Troubleshooting

### No data showing
```bash
curl https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector
curl https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector
```

### Collectors failing
```bash
gcloud functions logs read bluesky-collector --region=us-east4 --limit=20
gcloud functions logs read reddit-collector --region=us-east4 --limit=20
```

### Dashboard errors
```bash
gcloud run services logs read va11-dashboard --region=us-east4 --limit=50
```

## Next Steps

1. Share dashboard URL with Rep. Walkinshaw
2. Monitor data collection for 24 hours
3. Add YouTube collector (needs API key)
4. Implement 7-day backfill
5. Add policy issue categorization

## Support

GitHub: https://github.com/sbrow126/va11-intelligence-platform
