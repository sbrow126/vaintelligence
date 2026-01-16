# VA-11 Intelligence Platform

Real-time constituent intelligence dashboard for Representative James Walkinshaw (VA-11)

## 🎯 What This Is

A social media monitoring and sentiment analysis platform that:
- Collects posts from Bluesky, Mastodon, YouTube, Reddit
- Analyzes sentiment using Claude Sonnet AI
- Provides real-time dashboard showing constituent opinions
- Tracks policy issues and geographic trends
- Runs automated data collection every 6 hours

## 🏗️ Architecture

- **Frontend**: Modern HTML5 dashboard with Chart.js
- **Backend**: Python Flask API
- **Database**: Google Cloud SQL (PostgreSQL)
- **Data Collection**: Google Cloud Functions (Python)
- **Hosting**: Google Cloud Run
- **Automation**: Google Cloud Scheduler

## 📦 What's Included

```
va11-intelligence-platform/
├── app.py                  # Flask API server
├── requirements.txt        # Python dependencies
├── Procfile               # Cloud Run startup config
├── templates/
│   └── dashboard.html     # Dashboard UI
├── DEPLOYMENT.md          # Detailed deployment guide
├── README.md              # This file
└── .gitignore            # Git ignore rules
```

## 🚀 Quick Deployment

### Step 1: Push to GitHub

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: VA-11 Intelligence Platform"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/va11-intelligence-platform.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Google Cloud Run

```bash
# Make sure you're logged in to Google Cloud
gcloud auth login
gcloud config set project va11-intelligence

# Deploy the dashboard
cd ~/va11-intelligence-platform

gcloud run deploy va11-dashboard \
    --source . \
    --platform managed \
    --region us-east4 \
    --allow-unauthenticated \
    --set-env-vars=DB_NAME=va11_intelligence,DB_USER=postgres,CLOUD_SQL_CONNECTION_NAME=va11-intelligence:us-east4:va11-db \
    --set-secrets=DB_PASSWORD=db-password:latest \
    --add-cloudsql-instances=va11-intelligence:us-east4:va11-db \
    --project=va11-intelligence
```

### Step 3: Access Your Dashboard

Your dashboard will be available at:
**https://va11-dashboard-466254020344.us-east4.run.app**

## 🔧 Configuration

### Environment Variables

Set these in Google Cloud Run:

- `DB_NAME`: Database name (default: `va11_intelligence`)
- `DB_USER`: Database user (default: `postgres`)
- `CLOUD_SQL_CONNECTION_NAME`: Cloud SQL connection string
- `GCP_PROJECT`: Google Cloud project ID

### Secrets

Store these in Google Cloud Secret Manager:

- `db-password`: PostgreSQL database password
- `anthropic-api-key`: Anthropic API key for sentiment analysis
- `reddit-client-id`: Reddit API client ID
- `reddit-client-secret`: Reddit API client secret

## 📊 API Endpoints

The backend provides these REST APIs:

- `GET /` - Dashboard homepage
- `GET /api/stats` - Overall statistics (total posts, sentiment counts)
- `GET /api/timeseries?days=30` - Sentiment over time
- `GET /api/platforms` - Platform breakdown
- `GET /api/issues` - Policy issues analysis
- `GET /health` - Health check endpoint

## 🔄 Data Collection

Data is collected automatically every 6 hours via Google Cloud Functions:

- **Bluesky**: `@repwalkinshaw.bsky.social`
- **Mastodon**: Relevant VA-11 hashtags and accounts
- **YouTube**: Comments on official videos and local news
- **Reddit**: r/nova, r/fairfaxcounty, r/reston

Each collector:
1. Fetches new posts/comments
2. Stores raw content in Cloud SQL
3. Analyzes sentiment using Claude Sonnet
4. Categorizes policy issues
5. Updates dashboard data

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_NAME=va11_intelligence
export DB_USER=postgres
export DB_PASSWORD=your_password

# Run Flask app
python app.py

# Access at http://localhost:8080
```

## 📈 Dashboard Features

### Overview Tab
- Total posts collected
- Sentiment breakdown (positive/negative/neutral)
- 30-day sentiment timeline chart
- Platform distribution chart

### Policy Issues Tab (Coming Soon)
- Issue categorization
- Sentiment by issue
- Trending topics

### Geographic Tab (Coming Soon)
- Map view of constituent sentiment
- Zip code breakdown
- District boundaries

### Live Posts Tab (Coming Soon)
- Real-time feed of new posts
- Filtering by platform and sentiment
- Direct links to source content

### Analytics Tab (Coming Soon)
- Advanced metrics
- Engagement analysis
- Weekly/monthly reports

## 🔐 Security

- Dashboard is publicly accessible (no sensitive data displayed)
- API keys stored in Google Cloud Secret Manager
- Database credentials never exposed in code
- All connections use SSL/TLS
- Rate limiting on API endpoints

## 💰 Cost Estimate

Monthly running costs (~$10-15):

- Google Cloud Run: $5 (includes 2M requests free)
- Cloud SQL: $7-10 (db-f1-micro instance)
- Cloud Functions: FREE (2M invocations free)
- Cloud Scheduler: FREE (3 jobs free)
- Secret Manager: FREE (6 secrets free)
- Anthropic API: $2-5 (based on volume)

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Contact: Dr. Shallon Elizabeth Brown
- Email: contact@ctoadvisorpro.com

## 📝 License

Proprietary - Copyright © 2026 CTO Advisor Pro

---

**Built with ❤️ for Representative James Walkinshaw and the constituents of Virginia's 11th District**
