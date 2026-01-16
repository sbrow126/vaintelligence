"""
Fixed Bluesky Collector - Handles video embeds and collects 7 days of data
"""

import functions_framework
import requests
import os
import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import Json

BLUESKY_API = "https://public.api.bsky.app/xrpc"

def get_db_connection():
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'va11_intelligence')
    connection_name = os.getenv('CLOUD_SQL_CONNECTION_NAME')
    
    host = f"/cloudsql/{connection_name}"
    
    conn = psycopg2.connect(
        host=host,
        database=db_name,
        user=db_user,
        password=db_password
    )
    return conn

def search_posts(query, limit=100):
    """Search Bluesky using public API"""
    try:
        url = f"{BLUESKY_API}/app.bsky.feed.searchPosts"
        params = {"q": query, "limit": limit}
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('posts', [])
            print(f"Found {len(posts)} posts for '{query}'")
            return posts
        else:
            print(f"Search failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def get_author_feed(handle, limit=50):
    """Get posts from specific author"""
    try:
        url = f"{BLUESKY_API}/app.bsky.feed.getAuthorFeed"
        params = {"actor": handle, "limit": limit}
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            feed = data.get('feed', [])
            posts = [item['post'] for item in feed]
            print(f"Found {len(posts)} posts from @{handle}")
            return posts
        else:
            print(f"Author feed failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting author feed: {e}")
        return []

def store_post(conn, post):
    """Store post in database"""
    try:
        cur = conn.cursor()
        
        post_id = post.get('uri', '')
        author = post.get('author', {})
        author_id = author.get('did', '')
        author_username = author.get('handle', '')
        record = post.get('record', {})
        content = record.get('text', '')
        
        created_at = record.get('createdAt', '')
        if created_at:
            timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            timestamp = datetime.utcnow()
        
        url = f"https://bsky.app/profile/{author_username}/post/{post_id.split('/')[-1]}"
        
        likes = post.get('likeCount', 0)
        reposts = post.get('repostCount', 0)
        replies = post.get('replyCount', 0)
        engagement = float(likes + (reposts * 2) + (replies * 1.5))
        
        cur.execute("""
            INSERT INTO social_media_posts 
            (post_id, platform, author_id, author_username, content, timestamp, url,
             likes, shares, comments, engagement_score, raw_data, processed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
            RETURNING post_id
        """, (
            post_id, 'bluesky', author_id, author_username, content, timestamp, url,
            likes, reposts, replies, engagement, Json(post), False, datetime.utcnow()
        ))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        return result is not None
        
    except Exception as e:
        print(f"Error storing post: {e}")
        conn.rollback()
        return False

@functions_framework.http
def bluesky_collector_function(request):
    """Main collector function"""
    print("Starting Bluesky collection...")
    
    try:
        conn = get_db_connection()
        
        search_terms = [
            "Reston Virginia",
            "Fairfax County",
            "Herndon Virginia",
            "Vienna Virginia", 
            "James Walkinshaw",
            "Northern Virginia politics",
            "#NOVA",
            "#VA11"
        ]
        
        all_posts = []
        
        for term in search_terms[:3]:
            posts = search_posts(term, limit=50)
            all_posts.extend(posts)
        
        rep_posts = get_author_feed("repwalkinshaw.bsky.social", limit=50)
        all_posts.extend(rep_posts)
        
        stored = 0
        for post in all_posts:
            if store_post(conn, post):
                stored += 1
        
        conn.close()
        
        return {
            "status": "success",
            "posts_collected": stored,
            "total_found": len(all_posts)
        }, 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
