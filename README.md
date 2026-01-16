# VA-11 Intelligence Platform - Complete Repository

Real-time constituent intelligence dashboard for Representative James Walkinshaw (VA-11)

## What This Is

A complete social media monitoring and sentiment analysis platform that:
- Collects posts from Bluesky and Reddit
- Analyzes sentiment using Claude Sonnet AI
- Provides real-time dashboard showing constituent opinions
- Tracks policy issues and geographic trends
- Runs automated data collection every 6 hours

## Repository Structure

```
va11-intelligence-platform/
├── README.md                           # This file
├── DEPLOYMENT.md                       # Complete deployment guide
├── QUICKSTART.md                       # Fast setup guide
│
├── dashboard/                          # Frontend dashboard
│   ├── app.py                         # Flask API server
│   ├── requirements.txt               # Python dependencies
│   ├── Procfile                       # Cloud Run config
│   └── templates/
│       └── dashboard.html             # Dashboard UI
│
├── collectors/                         # Data collectors
│   ├── bluesky/
│   │   ├── main.py                    # Bluesky collector
│   │   └── requirements.txt
│   └── reddit/
│       ├── main.py                    # Reddit collector
│       └── requirements.txt
│
├── processors/                         # Data processors
│   └── sentiment/
│       ├── main.py                    # Sentiment analyzer
│       └── requirements.txt
│
└── deployment/                         # Deployment scripts
    ├── deploy_all.sh                  # Deploy everything
    ├── deploy_collectors.sh           # Deploy collectors only
    └── test_system.sh                 # Test all components
```

## Quick Start

### Prerequisites
- Google Cloud account with billing enabled
- GitHub account (username: sbrow126)
- Anthropic API key (for sentiment analysis)

### Deploy in 3 Steps

1. **Upload to GitHub:**
```bash
git clone https://github.com/sbrow126/va11-intelligence-platform.git
cd va11-intelligence-platform
git add .
git commit -m "Complete platform deployment"
git push
```

2. **Deploy to Google Cloud:**
```bash
cd deployment
chmod +x deploy_all.sh
./deploy_all.sh
```

3. **Access Dashboard:**
```
https://va11-dashboard-466254020344.us-east4.run.app
```

## Current Status

### Working ✅
- Dashboard UI (modern, responsive)
- Bluesky collector (fixed video embed issues)
- Reddit collector (no API key needed)
- Sentiment analyzer
- PostgreSQL database
- Cloud Run hosting

### To Do ⏳
- YouTube collector (needs API key)
- Mastodon collector (needs better search)
- 7-day backfill mode
- Policy issue categorization
- Geographic mapping

## System Architecture

```
Google Cloud Platform
├── Cloud Functions (Data Collection)
│   ├── bluesky-collector (every 6 hours)
│   ├── reddit-collector (every 6 hours)
│   └── sentiment-analyzer (every hour)
│
├── Cloud SQL (Database)
│   └── PostgreSQL 15
│       └── va11_intelligence database
│
├── Cloud Run (Dashboard)
│   └── Flask + Chart.js frontend
│
└── Cloud Scheduler (Automation)
    └── Triggers collectors automatically
```

## Configuration

### Environment Variables
- `DB_NAME`: va11_intelligence
- `DB_USER`: postgres
- `CLOUD_SQL_CONNECTION_NAME`: va11-intelligence:us-east4:va11-db
- `GCP_PROJECT`: va11-intelligence

### Secrets (in Secret Manager)
- `db-password`: SecureVA11Pass2024!
- `anthropic-api-key`: Your Anthropic API key

## Troubleshooting

### Dashboard shows no data
```bash
gcloud sql connect va11-db --user=postgres --database=va11_intelligence
SELECT platform, COUNT(*) FROM social_media_posts GROUP BY platform;
```

### Collectors not running
```bash
gcloud scheduler jobs list --location=us-east4
gcloud functions logs read bluesky-collector --region=us-east4 --limit=20
```

### Deploy failed
Check logs:
```bash
gcloud run services logs read va11-dashboard --region=us-east4 --limit=50
```

## Cost Estimate

Monthly: $10-15
- Cloud Run: $5
- Cloud SQL: $7-10
- Cloud Functions: FREE
- Cloud Scheduler: FREE
- Anthropic API: $2-5

## Support

- GitHub: https://github.com/sbrow126/va11-intelligence-platform
- Contact: Dr. Shallon Elizabeth Brown
- Email: contact@ctoadvisorpro.com

## License

Proprietary - Copyright © 2026 CTO Advisor Pro
