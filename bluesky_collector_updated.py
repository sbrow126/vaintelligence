"""
Bluesky Collector with 7-Day Backfill Support
Collects posts from Bluesky for VA-11 district monitoring
"""

import functions_framework
import requests
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import psycopg2

# Configuration
BLUESKY_API = "https://bsky.social/xrpc"

def get_db_connection():
    """Create PostgreSQL connection"""
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'va11_intelligence')
    connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
    
    # Use Unix socket for Cloud SQL
    host = f"/cloudsql/{connection_name}"
    
    conn = psycopg2.connect(
        host=host,
        database=db_name,
        user=db_user,
        password=db_password
    )
    return conn

def get_bluesky_session():
    """Authenticate with Bluesky and get session"""
    handle = os.getenv('BLUESKY_HANDLE')
    password = os.getenv('BLUESKY_PASSWORD')
    
    response = requests.post(
        f"{BLUESKY_API}/com.atproto.server.createSession",
        json={"identifier": handle, "password": password}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Bluesky auth failed: {response.text}")

def get_last_collection_time(conn):
    """Get the last time we collected Bluesky data"""
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(timestamp) FROM social_media_posts 
            WHERE platform = 'bluesky'
        """)
        result = cur.fetchone()
        cur.close()
        return result[0] if result[0] else None
    except:
        return None

def search_bluesky_posts(session, search_terms, since_date=None):
    """Search Bluesky for posts matching terms"""
    headers = {"Authorization": f"Bearer {session['accessJwt']}"}
    all_posts = []
    
    for term in search_terms:
        try:
            params = {
                "q": term,
                "limit": 100
            }
            
            # Add since parameter if we have a date
            if since_date:
                params["since"] = since_date.isoformat()
            
            response = requests.get(
                f"{BLUESKY_API}/app.bsky.feed.searchPosts",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('posts', [])
                print(f"Found {len(posts)} posts for term '{term}'")
                all_posts.extend(posts)
            else:
                print(f"Search failed for '{term}': {response.status_code}")
                
        except Exception as e:
            print(f"Error searching for '{term}': {e}")
            continue
    
    return all_posts

def get_user_posts(session, handle, since_date=None):
    """Get posts from a specific Bluesky user"""
    headers = {"Authorization": f"Bearer {session['accessJwt']}"}
    
    try:
        params = {"actor": handle, "limit": 100}
        
        response = requests.get(
            f"{BLUESKY_API}/app.bsky.feed.getAuthorFeed",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('feed', [])
            
            # Filter by date if specified
            if since_date:
                posts = [p for p in posts if datetime.fromisoformat(p['post']['indexedAt'].replace('Z', '+00:00')) >= since_date]
            
            print(f"Found {len(posts)} posts from @{handle}")
            return [p['post'] for p in posts]
        else:
            print(f"Failed to get posts from @{handle}: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error getting posts from @{handle}: {e}")
        return []

def store_post(conn, post, platform='bluesky'):
    """Store a single post in the database"""
    try:
        cur = conn.cursor()
        
        # Extract post data
        post_id = post.get('uri', post.get('cid', ''))
        author = post.get('author', {})
        author_id = author.get('did', '')
        author_username = author.get('handle', '')
        content = post.get('record', {}).get('text', post.get('text', ''))
        timestamp = post.get('indexedAt', post.get('createdAt', datetime.utcnow().isoformat()))
        
        # Convert timestamp to datetime
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        url = f"https://bsky.app/profile/{author_username}/post/{post_id.split('/')[-1]}"
        
        # Get engagement metrics
        like_count = post.get('likeCount', 0)
        repost_count = post.get('repostCount', 0)
        reply_count = post.get('replyCount', 0)
        
        # Calculate engagement score
        engagement_score = float(like_count + (repost_count * 2) + (reply_count * 1.5))
        
        # Insert post
        cur.execute("""
            INSERT INTO social_media_posts 
            (post_id, platform, author_id, author_username, content, timestamp, url,
             likes, shares, comments, engagement_score, raw_data, processed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
        """, (
            post_id, platform, author_id, author_username, content, timestamp, url,
            like_count, repost_count, reply_count, engagement_score,
            json.dumps(post), False, datetime.utcnow()
        ))
        
        conn.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error storing post: {e}")
        conn.rollback()
        return False

@functions_framework.http
def bluesky_collector_function(request):
    """Main collector function"""
    print("Starting Bluesky collection...")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Check if this is a backfill run
        backfill_days = int(os.getenv('BACKFILL_DAYS', '0'))
        
        if backfill_days > 0:
            # Backfill mode: collect last N days
            since_date = datetime.utcnow() - timedelta(days=backfill_days)
            print(f"BACKFILL MODE: Collecting {backfill_days} days of data since {since_date}")
        else:
            # Incremental mode: collect since last run
            last_collection = get_last_collection_time(conn)
            if last_collection:
                since_date = last_collection
                print(f"INCREMENTAL MODE: Collecting since {since_date}")
            else:
                # First run, collect last 7 days
                since_date = datetime.utcnow() - timedelta(days=7)
                print(f"FIRST RUN: Collecting 7 days of data since {since_date}")
        
        # Authenticate with Bluesky
        session = get_bluesky_session()
        
        # Search terms for VA-11 district
        search_terms = [
            "Reston VA",
            "Fairfax County",
            "Herndon VA",
            "Vienna VA",
            "James Walkinshaw",
            "#VA11",
            "#NOVA",
            "Northern Virginia"
        ]
        
        # Collect from search
        posts = search_bluesky_posts(session, search_terms, since_date)
        
        # Also collect from Rep. Walkinshaw's account
        rep_posts = get_user_posts(session, "repwalkinshaw.bsky.social", since_date)
        posts.extend(rep_posts)
        
        # Store all posts
        stored_count = 0
        for post in posts:
            if store_post(conn, post):
                stored_count += 1
        
        conn.close()
        
        result = {
            "status": "success",
            "posts_collected": stored_count,
            "total_found": len(posts),
            "mode": "backfill" if backfill_days > 0 else "incremental",
            "since_date": since_date.isoformat()
        }
        
        print(f"Collection complete: {result}")
        return result, 200
        
    except Exception as e:
        error_msg = f"Collection failed: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}, 500
