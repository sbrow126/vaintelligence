from flask import Flask, render_template, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from google.cloud import secretmanager

app = Flask(__name__)

# Database configuration
def get_secret(secret_id):
    """Get secret from Google Cloud Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get('GCP_PROJECT', 'va11-intelligence')
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

def get_db_connection():
    """Create database connection"""
    # Get connection details from environment
    db_host = os.environ.get('DB_HOST', '/cloudsql/' + os.environ.get('CLOUD_SQL_CONNECTION_NAME'))
    db_name = os.environ.get('DB_NAME', 'va11_intelligence')
    db_user = os.environ.get('DB_USER', 'postgres')
    
    # Get password from Secret Manager
    try:
        db_password = get_secret('db-password')
    except:
        db_password = os.environ.get('DB_PASSWORD', '')
    
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password
    )
    return conn

@app.route('/')
def index():
    """Serve main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total posts
        cur.execute("SELECT COUNT(*) as count FROM social_media_posts")
        total_posts = cur.fetchone()['count']
        
        # Get sentiment breakdown
        cur.execute("""
            SELECT 
                sentiment_category,
                COUNT(*) as count
            FROM sentiment_analysis
            GROUP BY sentiment_category
        """)
        sentiment = {row['sentiment_category']: row['count'] for row in cur.fetchall()}
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total_posts': total_posts,
            'positive_posts': sentiment.get('positive', 0),
            'negative_posts': sentiment.get('negative', 0),
            'neutral_posts': sentiment.get('neutral', 0)
        })
    except Exception as e:
        print(f"Error in /api/stats: {e}")
        return jsonify({
            'total_posts': 0,
            'positive_posts': 0,
            'negative_posts': 0,
            'neutral_posts': 0,
            'error': str(e)
        }), 500

@app.route('/api/timeseries')
def get_timeseries():
    """Get sentiment over time"""
    try:
        days = int(request.args.get('days', 30))
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                DATE(p.created_at) as date,
                SUM(CASE WHEN s.sentiment_category = 'positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN s.sentiment_category = 'negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN s.sentiment_category = 'neutral' THEN 1 ELSE 0 END) as neutral
            FROM social_media_posts p
            LEFT JOIN sentiment_analysis s ON p.post_id = s.post_id
            WHERE p.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(p.created_at)
            ORDER BY date
        """, (days,))
        
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify(results)
    except Exception as e:
        print(f"Error in /api/timeseries: {e}")
        return jsonify([]), 500

@app.route('/api/platforms')
def get_platforms():
    """Get platform breakdown"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                platform,
                COUNT(*) as count
            FROM social_media_posts
            GROUP BY platform
            ORDER BY count DESC
        """)
        
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify(results)
    except Exception as e:
        print(f"Error in /api/platforms: {e}")
        return jsonify([]), 500

@app.route('/api/issues')
def get_issues():
    """Get policy issues breakdown"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                issue_category,
                COUNT(*) as count,
                AVG(s.sentiment_score) as avg_sentiment
            FROM issue_categorization ic
            JOIN sentiment_analysis s ON ic.post_id = s.post_id
            GROUP BY issue_category
            ORDER BY count DESC
        """)
        
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify(results)
    except Exception as e:
        print(f"Error in /api/issues: {e}")
        return jsonify([]), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
