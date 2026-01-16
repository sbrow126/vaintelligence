# ⚡ QUICK START - Get Your Dashboard Live in 10 Minutes

## What You're About To Do

1. Download the files (you already have them!)
2. Push to GitHub
3. Redeploy to Google Cloud Run
4. See your new dashboard live!

## Step 1: Push to GitHub (3 minutes)

### If you have the vaintelligence repo already on GitHub:

```bash
# In Google Cloud Shell, go to your existing repo
cd ~/vaintelligence/dashboard

# Replace the old dashboard files with new ones
# (Copy the files from this package into ~/vaintelligence/dashboard)

# Commit and push
git add .
git commit -m "Updated to modern dashboard UI"
git push
```

### If starting fresh:

```bash
# In Google Cloud Shell
cd ~
mkdir va11-intelligence-platform
cd va11-intelligence-platform

# Upload all files from this package

# Initialize git
git init
git add .
git commit -m "Initial commit: VA-11 Intelligence Platform"

# Create repo on GitHub: https://github.com/new
# Then:
git remote add origin https://github.com/YOUR_USERNAME/va11-intelligence-platform.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Cloud Run (5 minutes)

```bash
# Make sure you're logged in
gcloud auth login
gcloud config set project va11-intelligence

# Navigate to your project
cd ~/va11-intelligence-platform  # or ~/vaintelligence/dashboard

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

## Step 3: Open Your Dashboard (1 minute)

```
https://va11-dashboard-466254020344.us-east4.run.app
```

**Done!** 🎉

## What You Should See

Your dashboard will show:
- ✅ Total posts collected
- ✅ Sentiment breakdown (positive/negative/neutral)
- ✅ 30-day sentiment timeline chart
- ✅ Platform distribution pie chart
- ✅ Last updated timestamp
- ✅ Navigation tabs for future features

## If Something Goes Wrong

### Dashboard shows "Error" or no data:

```bash
# Check if collectors are running
gcloud scheduler jobs list --location us-east4

# Manually trigger a collector
gcloud functions call collect-bluesky --region us-east4

# Wait 2 minutes, then refresh dashboard
```

### Database connection issues:

```bash
# Verify connection name
gcloud sql instances describe va11-db --format="value(connectionName)"

# Should show: va11-intelligence:us-east4:va11-db

# Check secret
gcloud secrets versions access latest --secret=db-password
```

### Still having issues?

Check the detailed troubleshooting in `DEPLOYMENT.md`

---

## What's Next?

Now that your dashboard is live, you can:

1. **Share with Rep. Walkinshaw** - Send him the URL
2. **Set up alerts** - Get notified of sentiment spikes
3. **Add authentication** - Protect with password (optional)
4. **Customize design** - Edit `templates/dashboard.html`
5. **Add features** - Implement Policy Issues, Geographic tabs

---

**You're done!** Your constituent intelligence platform is now live and collecting data every 6 hours.

Time to show Rep. Walkinshaw what his constituents are saying! 🚀
