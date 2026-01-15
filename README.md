# VA-11 Constituent Intelligence Platform

Real-time social media intelligence for Representative James Walkinshaw (VA-11)

## Quick Deploy to GCP

### Prerequisites
- GCP account with billing enabled
- Bluesky credentials

### Setup (45 minutes)

1. **Clone this repo in Cloud Shell**
```bash
git clone https://github.com/sbrow126/vaintelligence.git
cd vaintelligence
```

2. **Enable APIs**
```bash
export PROJECT_ID="va11-intelligence"
gcloud config set project $PROJECT_ID
gcloud services enable cloudfunctions.googleapis.com cloudscheduler.googleapis.com sqladmin.googleapis.com language.googleapis.com run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com
```

3. **Create Database**
```bash
gcloud sql instances create va11-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=us-east4 --root-password="SecurePassword123!" --project=va11-intelligence
gcloud sql databases create va11_intelligence --instance=va11-db --project=va11-intelligence
```

4. **Initialize Schema**
```bash
gcloud sql connect va11-db --user=postgres --project=va11-intelligence
# Password: SecurePassword123!
\i deployment/init_database.sql
\dt
\q
```

5. **Store Secrets**
```bash
echo -n "blackdragon10.bsky.social" | gcloud secrets create bluesky-handle --data-file=- --project=va11-intelligence
echo -n "qm3y-zy5j-bz37-ncdr" | gcloud secrets create bluesky-password --data-file=- --project=va11-intelligence
echo -n "SecurePassword123!" | gcloud secrets create db-password --data-file=- --project=va11-intelligence
```

6. **Deploy Everything**
```bash
cd deployment
chmod +x deploy.sh
./deploy.sh
```

## Features
- Bluesky social media monitoring
- GCP Natural Language sentiment analysis
- 12 policy topic categories
- Real-time dashboard
- Automated collection every 6 hours

## Cost
~$30-60/month on GCP

## Your Settings
- Project: va11-intelligence
- Region: us-east4
- DB: va11-db
- Bluesky: blackdragon10.bsky.social
