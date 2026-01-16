"""
Sentiment Analyzer using Claude Sonnet
"""

import functions_framework
import os
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
from anthropic import Anthropic

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

def get_unprocessed_posts(conn, limit=50):
    """Get posts that haven't been analyzed yet"""
    cur = conn.cursor()
    cur.execute("""
        SELECT post_id, content 
        FROM social_media_posts 
        WHERE processed = false 
        AND content IS NOT NULL 
        AND content != ''
        LIMIT %s
    """, (limit,))
    posts = cur.fetchall()
    cur.close()
    return posts

def analyze_sentiment(content):
    """Analyze sentiment using Claude"""
    try:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return 0.0, 'neutral'
        
        client = Anthropic(api_key=api_key)
        
        prompt = f"""Analyze the sentiment of this social media post. Respond with ONLY a JSON object with this exact format:
{{"score": <number between -1 and 1>, "category": "<positive, negative, or neutral>"}}

Post: {content[:500]}

JSON:"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        result = json.loads(response_text)
        
        score = float(result.get('score', 0.0))
        category = result.get('category', 'neutral').lower()
        
        if category not in ['positive', 'negative', 'neutral']:
            category = 'neutral'
        
        return score, category
        
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return 0.0, 'neutral'

def store_sentiment(conn, post_id, score, category):
    """Store sentiment analysis result"""
    try:
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO sentiment_analysis 
            (post_id, sentiment_score, sentiment_category, analysis_timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (post_id) 
            DO UPDATE SET 
                sentiment_score = EXCLUDED.sentiment_score,
                sentiment_category = EXCLUDED.sentiment_category,
                analysis_timestamp = EXCLUDED.analysis_timestamp
        """, (post_id, score, category, datetime.utcnow()))
        
        cur.execute("""
            UPDATE social_media_posts 
            SET processed = true 
            WHERE post_id = %s
        """, (post_id,))
        
        conn.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error storing sentiment: {e}")
        conn.rollback()
        return False

@functions_framework.http
def sentiment_analyzer_function(request):
    """Main sentiment analyzer function"""
    print("Starting sentiment analysis...")
    
    try:
        conn = get_db_connection()
        
        posts = get_unprocessed_posts(conn, limit=50)
        
        if not posts:
            conn.close()
            return {"status": "success", "posts_analyzed": 0, "message": "No unprocessed posts"}, 200
        
        analyzed = 0
        for post_id, content in posts:
            score, category = analyze_sentiment(content)
            if store_sentiment(conn, post_id, score, category):
                analyzed += 1
        
        conn.close()
        
        return {
            "status": "success",
            "posts_analyzed": analyzed,
            "total_found": len(posts)
        }, 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
