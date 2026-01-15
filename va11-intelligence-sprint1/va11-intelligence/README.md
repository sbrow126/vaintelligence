# VA-11 Constituent Intelligence Platform

Real-time social media intelligence for Representative James Walkinshaw (VA-11)

## 🎯 Features

- **Multi-Platform Monitoring**: Reddit, Bluesky (with Facebook, Instagram, YouTube coming in Phase 2)
- **Sentiment Analysis**: Powered by GCP Natural Language API
- **Topic Classification**: Automatic categorization into 12 policy areas
- **Real-Time Dashboard**: Streamlit-based visualization
- **Automated Collection**: Cloud Functions run every 6 hours
- **Trend Detection**: Identify emerging issues before they escalate

## 🏗️ Architecture

```
Data Collection (Cloud Functions, scheduled every 6 hours)
    ↓
Raw Data Storage (Cloud SQL PostgreSQL)
    ↓
Sentiment Analysis (GCP Natural Language API)
    ↓
Dashboard (Streamlit on Cloud Run)
```

## 📋 Prerequisites

1. **GCP Account** with billing enabled
2. **Reddit API Credentials**:
   - Go to https://www.reddit.com/prefs/apps
   - Create an app (script type)
   - Note client_id and client_secret
3. **Bluesky Account**:
   - Create account at https://bsky.app
   - Generate app password in settings
4. **Local Development**:
   - Python 3.11+
   - PostgreSQL (for local testing)

## 🚀 Quick Start (Local Development)

### 1. Clone and Setup

```bash
# Create project directory
mkdir va11-intelligence
cd va11-intelligence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Fill in:
- Reddit API credentials
- Bluesky credentials
- Database connection details

### 3. Initialize Database

```bash
# Create database
createdb va11_intelligence

# Initialize schema
python database/models.py
```

### 4. Test Data Collection

```bash
# Test Reddit collector
python collectors/reddit_collector.py

# Test Bluesky collector
python collectors/bluesky_collector.py

# Test sentiment analyzer
python processors/sentiment_analyzer.py
```

### 5. Run Dashboard

```bash
cd dashboard
streamlit run app.py
```

Visit http://localhost:8501

## ☁️ Production Deployment on GCP

### Step 1: Create GCP Project

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable language.googleapis.com
gcloud services enable run.googleapis.com
```

### Step 2: Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create va11-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-east4 \
    --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create va11_intelligence --instance=va11-db

# Get connection name
gcloud sql instances describe va11-db --format='value(connectionName)'
```

### Step 3: Store Secrets

```bash
# Reddit credentials
echo -n "your-reddit-client-id" | gcloud secrets create reddit-client-id --data-file=-
echo -n "your-reddit-client-secret" | gcloud secrets create reddit-client-secret --data-file=-

# Bluesky credentials
echo -n "your.handle.bsky.social" | gcloud secrets create bluesky-handle --data-file=-
echo -n "your-app-password" | gcloud secrets create bluesky-password --data-file=-
```

### Step 4: Deploy Cloud Functions

See `deployment/DEPLOYMENT.md` for detailed deployment commands.

Quick deploy:
```bash
# Deploy all functions
./deployment/deploy_all.sh
```

### Step 5: Set Up Scheduling

```bash
# Create scheduler jobs (run every 6 hours)
./deployment/setup_scheduler.sh
```

### Step 6: Deploy Dashboard

```bash
# Deploy Streamlit dashboard to Cloud Run
gcloud run deploy va11-dashboard \
    --source dashboard/ \
    --platform managed \
    --region us-east4 \
    --allow-unauthenticated
```

## 📊 Dashboard Features

### Executive Overview
- Total mentions across platforms
- Average sentiment score
- Total engagement metrics
- Unique constituent voices

### Top Issues
- Issue mention volume
- Sentiment by issue
- Trending topics

### Sentiment Trends
- Daily sentiment tracking
- Mention volume over time
- Emerging patterns

### High-Engagement Posts
- Most-discussed posts
- Sentiment breakdown
- Direct links to original content

### Platform Analytics
- Distribution across platforms
- Platform-specific sentiment
- Engagement comparisons

## 🔧 Maintenance

### Monitor Cloud Functions
```bash
# View logs
gcloud functions logs read reddit-collector --region=us-east4 --limit=50

# Check execution status
gcloud scheduler jobs describe reddit-collection-job --location=us-east4
```

### Database Management
```bash
# Connect to Cloud SQL
gcloud sql connect va11-db --user=postgres

# Backup database
gcloud sql backups create --instance=va11-db
```

### Update Functions
```bash
# Redeploy after code changes
gcloud functions deploy reddit-collector \
    --source collectors/ \
    --runtime python311 \
    --region us-east4
```

## 💰 Cost Estimate

- **Cloud Functions**: $5-10/month (generous free tier)
- **Cloud SQL** (db-f1-micro): $15-20/month
- **Cloud Run** (dashboard): $0-5/month (usually free tier)
- **Natural Language API**: $10-30/month
- **Cloud Scheduler**: $0.10/month
- **Total: ~$30-65/month**

## 🔐 Security Best Practices

1. **Use Secret Manager** for all credentials
2. **Enable VPC** for Cloud SQL connections
3. **Restrict function access** with IAM
4. **Enable Cloud Armor** for dashboard if public
5. **Regular backups** of database
6. **Monitor costs** with billing alerts

## 📈 Scaling to $10K/Month Value

### Phase 2 Additions (Week 2-3):
- Facebook/Instagram/YouTube integration
- Predictive analytics/early warning system
- Competitive intelligence (other VA districts)
- Automated weekly briefings

### Phase 3 Additions (Week 4+):
- Legislative impact tracking
- Influencer network mapping
- Demographic deep-dives
- Crisis communication dashboard

## 🤝 Support

Built by Dr. Shallon Brown
- Email: sbrown@ctoadvisorpro.com
- LinkedIn: [Your LinkedIn]
- GitHub: [Your GitHub]

## 📝 License

Proprietary - Built for Representative James Walkinshaw

## 🎯 Next Steps

1. ✅ Complete Sprint 1 (Reddit + Bluesky)
2. ⏳ Demo to James Walkinshaw
3. ⏳ Sprint 2 (YouTube + Facebook + Instagram)
4. ⏳ Sprint 3 (Twitter/X + Threads)
5. ⏳ Advanced analytics and predictions
6. ⏳ White-label for other state reps

---

**Version**: 1.0.0 (Sprint 1 - Reddit & Bluesky MVP)
**Last Updated**: January 2026
