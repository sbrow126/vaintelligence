#!/bin/bash

echo "========================================="
echo "VA-11 Intelligence Platform Diagnostics"
echo "========================================="
echo ""

# Set project
gcloud config set project va11-intelligence

echo "1. Checking deployed Cloud Functions..."
echo "========================================"
gcloud functions list --gen2 --region=us-east4 --project=va11-intelligence

echo ""
echo "2. Checking Cloud Scheduler Jobs..."
echo "========================================"
gcloud scheduler jobs list --location=us-east4 --project=va11-intelligence

echo ""
echo "3. Testing each collector..."
echo "========================================"

echo "Testing Bluesky collector..."
curl -s https://us-east4-va11-intelligence.cloudfunctions.net/bluesky-collector | jq '.'

echo ""
echo "Testing Mastodon collector..."
curl -s https://us-east4-va11-intelligence.cloudfunctions.net/mastodon-collector | jq '.'

echo ""
echo "Testing YouTube collector (if deployed)..."
curl -s https://us-east4-va11-intelligence.cloudfunctions.net/youtube-collector | jq '.'

echo ""
echo "Testing Reddit collector (if deployed)..."
curl -s https://us-east4-va11-intelligence.cloudfunctions.net/reddit-collector | jq '.'

echo ""
echo "4. Checking database for post counts..."
echo "========================================"
echo "Run this in Cloud SQL:"
echo "SELECT platform, COUNT(*) as count, MAX(timestamp) as latest_post FROM social_media_posts GROUP BY platform ORDER BY count DESC;"

echo ""
echo "========================================="
echo "Diagnostics Complete!"
echo "========================================="
