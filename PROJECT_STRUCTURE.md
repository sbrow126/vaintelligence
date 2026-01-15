# VA-11 Intelligence Platform - Project Structure

```
va11-intelligence/
│
├── README.md                          # Main documentation
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── test_setup.py                      # Local testing script
│
├── database/
│   └── models.py                      # SQLAlchemy database models
│
├── collectors/                        # Data collection modules
│   ├── reddit_collector.py            # Reddit API integration
│   └── bluesky_collector.py           # Bluesky AT Protocol integration
│
├── processors/                        # Data processing modules
│   └── sentiment_analyzer.py          # GCP Natural Language API integration
│
├── dashboard/                         # Streamlit dashboard
│   └── app.py                         # Main dashboard interface
│
└── deployment/                        # GCP deployment configs
    └── DEPLOYMENT.md                  # Deployment instructions
```

## Database Schema

### Core Tables:
- `social_media_posts` - Raw posts from all platforms
- `sentiment_analysis` - Sentiment scores and entity extraction
- `topics` - Issue categories (housing, education, etc.)
- `post_topics` - Many-to-many relationship
- `influencers` - Key voices in the district
- `trend_tracking` - Historical trends
- `alerts` - System-generated alerts
- `demographics` - Census data by zip code
- `geographic_activity` - Location-based post mapping
- `legislative_activity` - Walkinshaw's bills and votes
- `legislative_sentiment` - Constituent response to legislation

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     CLOUD SCHEDULER                         │
│              (Triggers every 6 hours)                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├──────────────────────────────────────────┐
                 │                                          │
    ┌────────────▼──────────┐              ┌───────────────▼──────────┐
    │   Reddit Collector    │              │   Bluesky Collector      │
    │   (Cloud Function)    │              │   (Cloud Function)       │
    └────────────┬──────────┘              └───────────────┬──────────┘
                 │                                         │
                 └──────────────┬──────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   Cloud SQL            │
                    │   (PostgreSQL)         │
                    │   social_media_posts   │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │  Sentiment Analyzer     │
                    │  (Cloud Function)       │
                    │  + GCP Natural Lang API │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   sentiment_analysis   │
                    │   post_topics          │
                    │   (PostgreSQL)         │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   Streamlit Dashboard  │
                    │   (Cloud Run)          │
                    │   Real-time Analytics  │
                    └────────────────────────┘
```

## Key Features Implemented (Sprint 1)

### ✅ Data Collection
- Reddit monitoring (r/nova, r/fairfaxcounty, r/reston, r/Virginia)
- Bluesky search and timeline monitoring
- Automated every 6 hours
- Location extraction
- Engagement metrics tracking

### ✅ Sentiment Analysis
- GCP Natural Language API integration
- Sentiment scoring (-1 to 1)
- Entity extraction
- Content categorization

### ✅ Topic Classification
- 12 predefined policy areas
- Keyword matching
- Entity-based relevance scoring
- Automatic tagging

### ✅ Dashboard
- Executive metrics (mentions, sentiment, engagement)
- Top issues visualization
- Sentiment trends over time
- High-engagement posts
- Platform distribution
- Time-range filtering

## What's Working Now

After completing Sprint 1 setup, you'll have:
1. ✅ Automated data collection from Reddit + Bluesky
2. ✅ Real-time sentiment analysis
3. ✅ Topic categorization into 12 policy areas
4. ✅ Interactive dashboard with key metrics
5. ✅ Historical trend tracking
6. ✅ Geographic tagging by VA-11 communities

## Next Phases

### Sprint 2 (Week 2): Meta Ecosystem
- Facebook Groups integration
- Instagram monitoring
- YouTube comments
- Enhanced demographics

### Sprint 3 (Week 3): Advanced Features
- Twitter/X (if budget allows)
- Threads integration
- Predictive analytics
- Early warning system
- Competitive intelligence

### Sprint 4 (Week 4): Professional Features
- Influencer network mapping
- Legislative impact tracking
- Automated weekly briefings
- Crisis communication dashboard

## Cost Breakdown (Sprint 1)

- Cloud Functions: $5-10/month
- Cloud SQL: $15-20/month
- Natural Language API: $10-30/month
- Cloud Scheduler: $0.10/month
- Cloud Run (dashboard): $0-5/month
**Total: ~$30-65/month**

## Performance Specs

- **Collection frequency**: Every 6 hours
- **Processing latency**: ~15 minutes end-to-end
- **Dashboard refresh**: Real-time
- **Data retention**: Unlimited (configurable)
- **Platforms covered**: 2 (Reddit, Bluesky)
- **Geographic coverage**: VA-11 (Fairfax County)
- **Topics tracked**: 12 policy areas

## Security & Privacy

- ✅ All credentials in Secret Manager
- ✅ Public data only
- ✅ No personal identification
- ✅ Compliant with platform ToS
- ✅ Automated backups
- ✅ IAM-based access control
