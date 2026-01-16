# Complete Deployment Guide

## Prerequisites

✅ You already have:
- Google Cloud project: `va11-intelligence`
- Cloud SQL database: `va11-db`
- Database: `va11_intelligence`
- Cloud Functions deployed (Bluesky, Mastodon, YouTube, Reddit collectors)
- Cloud Scheduler jobs running
- GitHub account

## Step-by-Step Deployment

### 1. Upload to GitHub (5 minutes)

#### Option A: Using Git Command Line

```bash
# Navigate to the project directory
cd /path/to/va11-intelligence-platform

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: VA-11 Intelligence Platform"

# Create repository on GitHub (https://github.com/new)
# Name it: va11-intelligence-platform
# Make it PRIVATE

# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/va11-intelligence-platform.git

# Push to GitHub
git branch -M main
git push -u origin main
```

#### Option B: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `va11-intelligence-platform`
3. Select **Private**
4. Click "Create repository"
5. Click "uploading an existing file"
6. Drag and drop all files from this folder
7. Click "Commit changes"

### 2. Deploy to Google Cloud Run (10 minutes)

#### Method 1: Direct Deploy from Cloud Shell

```bash
# Log in to Google Cloud
gcloud auth login

# Set your project
gcloud config set project va11-intelligence

# Navigate to your project directory
# If on Cloud Shell, clone from GitHub:
git clone https://github.com/YOUR_USERNAME/va11-intelligence-platform.git
cd va11-intelligence-platform

# Deploy!
gcloud run deploy va11-dashboard \
    --source . \
    --platform managed \
    --region us-east4 \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=va11_intelligence,DB_USER=postgres,CLOUD_SQL_CONNECTION_NAME=va11-intelligence:us-east4:va11-db,GCP_PROJECT=va11-intelligence \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --add-cloudsql-instances=va11-intelligence:us-east4:va11-db \
    --project=va11-intelligence
```

#### Method 2: Deploy from GitHub

1. Go to Google Cloud Console: https://console.cloud.google.com
2. Navigate to **Cloud Run**
3. Click **Create Service**
4. Select **Continuously deploy from a repository (source-based)**
5. Click **Set up with Cloud Build**
6. Select **GitHub** as repository provider
7. Authenticate with GitHub
8. Select your repository: `va11-intelligence-platform`
9. Branch: `main`
10. Build type: **Dockerfile or Buildpack**
11. Click **Save**

Configure the service:
- Service name: `va11-dashboard`
- Region: `us-east4`
- Authentication: **Allow unauthenticated invocations**
- Container port: `8080`

Add environment variables:
- `DB_NAME` = `va11_intelligence`
- `DB_USER` = `postgres`
- `CLOUD_SQL_CONNECTION_NAME` = `va11-intelligence:us-east4:va11-db`
- `GCP_PROJECT` = `va11-intelligence`

Add secrets:
- `DB_PASSWORD` → Mount as environment variable from Secret Manager

Add Cloud SQL connection:
- Instance: `va11-intelligence:us-east4:va11-db`

Click **Create**.

### 3. Verify Deployment (2 minutes)

Once deployment completes, you'll get a URL like:
```
https://va11-dashboard-466254020344.us-east4.run.app
```

Test the endpoints:

```bash
# Health check
curl https://va11-dashboard-466254020344.us-east4.run.app/health

# Stats
curl https://va11-dashboard-466254020344.us-east4.run.app/api/stats

# Time series
curl https://va11-dashboard-466254020344.us-east4.run.app/api/timeseries?days=7
```

Open the dashboard in your browser:
```
https://va11-dashboard-466254020344.us-east4.run.app
```

### 4. Configure Custom Domain (Optional)

If you want a custom domain like `intelligence.jameswalkinshaw.com`:

1. In Cloud Run, click your service
2. Go to **"Manage Custom Domains"**
3. Click **"Add Mapping"**
4. Select your domain
5. Follow DNS configuration instructions

## Troubleshooting

### "Service Unavailable" Error

Check logs:
```bash
gcloud run services logs read va11-dashboard \
    --region us-east4 \
    --project va11-intelligence \
    --limit 50
```

Common issues:
- Database connection string incorrect
- Secret Manager permissions not set
- Cloud SQL instance name wrong

### No Data Showing

1. Check if collectors are running:
```bash
gcloud scheduler jobs list --location us-east4 --project va11-intelligence
```

2. Verify database has data:
```bash
# Connect to Cloud SQL
gcloud sql connect va11-db --user=postgres --database=va11_intelligence

# Check post count
SELECT COUNT(*) FROM social_media_posts;

# Check sentiment analysis
SELECT COUNT(*) FROM sentiment_analysis;
```

3. Manually trigger a collector:
```bash
gcloud functions call collect-bluesky \
    --region us-east4 \
    --project va11-intelligence
```

### Database Connection Issues

Verify Cloud SQL connection name:
```bash
gcloud sql instances describe va11-db \
    --project va11-intelligence \
    --format="value(connectionName)"
```

Should return: `va11-intelligence:us-east4:va11-db`

Verify secret is accessible:
```bash
gcloud secrets versions access latest \
    --secret=db-password \
    --project=va11-intelligence
```

### Charts Not Loading

Check browser console for JavaScript errors:
1. Open dashboard
2. Right-click → Inspect
3. Go to Console tab
4. Look for API errors

Verify Chart.js is loading:
- Check browser Network tab
- Look for `chart.umd.min.js` request
- Should return 200 OK

## Updating the Dashboard

### Update via GitHub

1. Make changes to files
2. Commit and push:
```bash
git add .
git commit -m "Updated dashboard design"
git push
```

3. Redeploy:
```bash
gcloud run deploy va11-dashboard \
    --source . \
    --platform managed \
    --region us-east4 \
    --project=va11-intelligence
```

### Update via Cloud Shell

1. Open Google Cloud Shell
2. Navigate to project:
```bash
cd ~/vaintelligence/dashboard
```

3. Make changes to files
4. Redeploy:
```bash
gcloud run deploy va11-dashboard \
    --source . \
    --platform managed \
    --region us-east4 \
    --project=va11-intelligence
```

## Monitoring

### View Logs

```bash
# Real-time logs
gcloud run services logs tail va11-dashboard \
    --region us-east4 \
    --project va11-intelligence

# Recent logs
gcloud run services logs read va11-dashboard \
    --region us-east4 \
    --project va11-intelligence \
    --limit 100
```

### Check Metrics

1. Go to Cloud Run console
2. Click on `va11-dashboard`
3. View **Metrics** tab for:
   - Request count
   - Request latency
   - Error rate
   - Container instances

### Set Up Alerts

1. Go to **Monitoring** in Cloud Console
2. Create alert policy:
   - Metric: Cloud Run Request Count
   - Condition: Error rate > 5%
   - Notification: Email

## Maintenance

### Update Dependencies

```bash
# Update requirements.txt with new versions
pip install --upgrade Flask gunicorn psycopg2-binary google-cloud-secret-manager

# Regenerate requirements.txt
pip freeze > requirements.txt

# Commit and redeploy
git add requirements.txt
git commit -m "Updated dependencies"
git push

# Redeploy
gcloud run deploy va11-dashboard --source . --region us-east4
```

### Database Maintenance

```bash
# Connect to database
gcloud sql connect va11-db --user=postgres --database=va11_intelligence

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Archive old posts (older than 90 days)
DELETE FROM social_media_posts WHERE created_at < NOW() - INTERVAL '90 days';

# Vacuum database
VACUUM ANALYZE;
```

## Security Best Practices

1. **Never commit secrets** - Use Secret Manager
2. **Keep dependencies updated** - Run security audits
3. **Monitor logs** - Check for suspicious activity
4. **Use IAM roles** - Least privilege principle
5. **Enable audit logging** - Track all changes

## Cost Optimization

Current costs (~$10-15/month):

To reduce costs:
1. Use Cloud SQL Backup scheduling (not continuous)
2. Reduce collector frequency (from 6 hours to 12 hours)
3. Implement data retention policy (delete posts > 90 days)
4. Use Cloud Run minimum instances = 0

## Next Steps

1. ✅ Deploy dashboard
2. ⏳ Add authentication (optional)
3. ⏳ Implement additional tabs (Policy Issues, Geographic)
4. ⏳ Add export functionality (CSV/PDF reports)
5. ⏳ Create weekly email digest
6. ⏳ Add real-time notifications for negative sentiment spikes

---

**Need help?** Open an issue on GitHub or contact Dr. Shallon Elizabeth Brown at contact@ctoadvisorpro.com
