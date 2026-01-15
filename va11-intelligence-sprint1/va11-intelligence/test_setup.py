#!/usr/bin/env python3
"""
Local Setup and Test Script for VA-11 Intelligence Platform
Run this to verify your setup before deploying to GCP
"""

import os
import sys
from datetime import datetime

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def check_environment():
    """Check if environment variables are set"""
    print_section("Checking Environment Variables")
    
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USER_AGENT',
        'BLUESKY_HANDLE',
        'BLUESKY_PASSWORD',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} required environment variables!")
        print("Please set them in your .env file or environment.")
        return False
    
    print("\n✅ All environment variables configured!")
    return True

def test_database_connection():
    """Test database connectivity"""
    print_section("Testing Database Connection")
    
    try:
        from database.models import get_connection_string, init_db
        
        print("Attempting to connect to database...")
        engine = init_db(get_connection_string())
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print(f"✅ Database connection successful!")
            print(f"   Connection string: {get_connection_string().split('@')[1]}")  # Hide password
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed!")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check your DB_* environment variables")
        print("3. Verify database exists: createdb va11_intelligence")
        return False

def initialize_database():
    """Initialize database schema"""
    print_section("Initializing Database Schema")
    
    try:
        from database.models import get_connection_string, init_db
        
        print("Creating tables...")
        engine = init_db(get_connection_string())
        print("✅ Database schema initialized!")
        
        # Count tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed!")
        print(f"   Error: {e}")
        return False

def test_reddit_collector():
    """Test Reddit data collection"""
    print_section("Testing Reddit Collector")
    
    try:
        print("Importing Reddit collector...")
        from collectors.reddit_collector import RedditCollector
        
        print("Initializing collector...")
        collector = RedditCollector()
        
        print("Testing connection to Reddit API...")
        subreddit = collector.reddit.subreddit('nova')
        print(f"✅ Connected to r/nova (subscribers: {subreddit.subscribers:,})")
        
        print("\nCollecting sample posts (this may take a minute)...")
        count = collector.collect_subreddit_posts('nova', limit=10)
        print(f"✅ Collected {count} relevant posts!")
        
        collector.close()
        return True
        
    except Exception as e:
        print(f"❌ Reddit collector test failed!")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your Reddit API credentials")
        print("2. Check that you created a Reddit app at https://www.reddit.com/prefs/apps")
        return False

def test_bluesky_collector():
    """Test Bluesky data collection"""
    print_section("Testing Bluesky Collector")
    
    try:
        print("Importing Bluesky collector...")
        from collectors.bluesky_collector import BlueskCollector
        
        print("Initializing collector...")
        collector = BlueskCollector()
        print("✅ Logged into Bluesky!")
        
        print("\nSearching for VA-11 posts (this may take a minute)...")
        count = collector.search_posts('Virginia', limit=10)
        print(f"✅ Found and collected {count} relevant posts!")
        
        collector.close()
        return True
        
    except Exception as e:
        print(f"❌ Bluesky collector test failed!")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your Bluesky handle and app password")
        print("2. Generate an app password at https://bsky.app/settings/app-passwords")
        return False

def test_sentiment_analyzer():
    """Test sentiment analysis"""
    print_section("Testing Sentiment Analyzer")
    
    try:
        print("Importing sentiment analyzer...")
        from processors.sentiment_analyzer import SentimentAnalyzer
        
        print("Initializing analyzer...")
        analyzer = SentimentAnalyzer()
        
        # Test with sample text
        print("\nTesting with sample text...")
        sample_text = "I love living in Reston! The parks are beautiful and the community is wonderful."
        result = analyzer.analyze_sentiment(sample_text)
        
        if result:
            print(f"✅ Sentiment analysis working!")
            print(f"   Score: {result['sentiment_score']:.2f} (Range: -1 to 1)")
            print(f"   Magnitude: {result['sentiment_magnitude']:.2f}")
            print(f"   Entities found: {len(result['entities'])}")
        else:
            print("❌ Sentiment analysis returned no results")
            return False
        
        analyzer.close()
        return True
        
    except Exception as e:
        print(f"❌ Sentiment analyzer test failed!")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure GCP credentials are configured")
        print("2. Enable Natural Language API in your GCP project")
        print("3. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        return False

def run_full_pipeline():
    """Run the complete data collection and analysis pipeline"""
    print_section("Running Full Pipeline Test")
    
    print("This will:")
    print("1. Collect posts from Reddit and Bluesky")
    print("2. Analyze sentiment for all posts")
    print("3. Categorize by topic")
    print("\nThis may take 2-3 minutes...")
    
    input("\nPress Enter to continue or Ctrl+C to skip...")
    
    try:
        # Collect from Reddit
        print("\n[1/3] Collecting from Reddit...")
        from collectors.reddit_collector import main as reddit_main
        reddit_result = reddit_main()
        print(f"   Collected: {reddit_result['posts_collected']} posts")
        
        # Collect from Bluesky
        print("\n[2/3] Collecting from Bluesky...")
        from collectors.bluesky_collector import main as bluesky_main
        bluesky_result = bluesky_main()
        print(f"   Collected: {bluesky_result['posts_collected']} posts")
        
        # Analyze sentiment
        print("\n[3/3] Analyzing sentiment...")
        from processors.sentiment_analyzer import main as sentiment_main
        sentiment_result = sentiment_main()
        print(f"   Analyzed: {sentiment_result['posts_processed']} posts")
        
        print("\n✅ Full pipeline completed successfully!")
        print(f"   Total posts collected: {reddit_result['posts_collected'] + bluesky_result['posts_collected']}")
        print(f"   Total posts analyzed: {sentiment_result['posts_processed']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed!")
        print(f"   Error: {e}")
        return False

def main():
    """Main test runner"""
    print("\n" + "🏛️ "*30)
    print("  VA-11 Constituent Intelligence Platform")
    print("  Local Setup and Test Suite")
    print("🏛️ "*30)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("\n✅ Loaded .env file")
    except ImportError:
        print("\n⚠️  python-dotenv not installed, using system environment variables")
    
    # Run tests
    tests = [
        ("Environment Variables", check_environment),
        ("Database Connection", test_database_connection),
        ("Database Schema", initialize_database),
        ("Reddit Collector", test_reddit_collector),
        ("Bluesky Collector", test_bluesky_collector),
        ("Sentiment Analyzer", test_sentiment_analyzer),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is ready.")
        print("\nNext steps:")
        print("1. Run the dashboard: cd dashboard && streamlit run app.py")
        print("2. Deploy to GCP: See deployment/DEPLOYMENT.md")
        print("3. Run full pipeline test (optional)")
        
        response = input("\nRun full pipeline test now? (y/n): ")
        if response.lower() == 'y':
            run_full_pipeline()
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before deploying.")
        print("Run this script again after making fixes.")
        sys.exit(1)

if __name__ == "__main__":
    main()
