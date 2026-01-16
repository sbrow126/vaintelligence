"""
Reddit Collector for VA-11 District
"""

import functions_framework
import requests
import os
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

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

def search_reddit(subreddit, query, limit=100):
    """Search Reddit using public JSON API"""
    try:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "1",
            "limit": limit,
            "sort": "new"
        }
        headers = {"User-Agent": "VA11Intelligence/1.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            print(f"Found {len(posts)} posts in r/{subreddit} for '{query}'")
            return [p['data'] for p in posts]
        else:
            print(f"Reddit search failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error searching Reddit: {e}")
        return []

def get_subreddit_new(subreddit, limit=50):
    """Get recent posts from subreddit"""
    try:
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        params = {"limit": limit}
        headers = {"User-Agent": "VA11Intelligence/1.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            print(f"Found {len(posts)} new posts in r/{subreddit}")
            return [p['data'] for p in posts]
        else:
            print(f"Subreddit fetch failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting subreddit: {e}")
        return []

def store_post(conn, post):
    """Store Reddit post in database"""
    try:
        cur = conn.cursor()
        
        post_id = f"reddit_{post.get('id', '')}"
        author = post.get('author', '[deleted]')
        title = post.get('title', '')
        selftext = post.get('selftext', '')
        content = f"{title}\n\n{selftext}" if selftext else title
        
        created_utc = post.get('created_utc', 0)
        timestamp = datetime.fromtimestamp(created_utc)
        
        url = f"https://reddit.com{post.get('permalink', '')}"
        
        ups = post.get('ups', 0)
        num_comments = post.get('num_comments', 0)
        engagement = float(ups + (num_comments * 2))
        
        cur.execute("""
            INSERT INTO social_media_posts 
            (post_id, platform, author_id, author_username, content, timestamp, url,
             likes, shares, comments, engagement_score, raw_data, processed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING
            RETURNING post_id
        """, (
            post_id, 'reddit', author, author, content, timestamp, url,
            ups, 0, num_comments, engagement, Json(post), False, datetime.utcnow()
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
def reddit_collector_function(request):
    """Main Reddit collector"""
    print("Starting Reddit collection...")
    
    try:
        conn = get_db_connection()
        
        subreddits = ["nova", "fairfaxcounty", "reston", "northernvirginia"]
        keywords = ["Reston", "Fairfax", "Herndon", "Vienna", "Northern Virginia"]
        
        all_posts = []
        
        for sub in subreddits:
            new_posts = get_subreddit_new(sub, limit=25)
            all_posts.extend(new_posts)
        
        for sub in subreddits[:2]:
            for keyword in keywords[:2]:
                search_posts = search_reddit(sub, keyword, limit=10)
                all_posts.extend(search_posts)
        
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
