"""Bluesky collector for VA-11"""
from atproto import Client
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('..')
from database.models import SocialMediaPost, get_connection_string, init_db
import json

class BlueskyCollector:
    def __init__(self):
        self.client = Client()
        self.client.login(os.getenv('BLUESKY_HANDLE'), os.getenv('BLUESKY_PASSWORD'))
        self.search_terms = ['VA-11', 'Fairfax County', 'Reston', 'Herndon', 'Vienna', 'Walkinshaw', 'Northern Virginia']
        engine = init_db(get_connection_string())
        Session = sessionmaker(bind=engine)
        self.db_session = Session()
    
    def extract_location(self, text):
        if not text: return None, None
        locations = {'Reston': '20190', 'Herndon': '20170', 'Vienna': '22180', 'Oakton': '22124', 'Great Falls': '22066', 'McLean': '22101', 'Tysons': '22102', 'Fairfax': '22030'}
        text_lower = text.lower()
        for location, zip_code in locations.items():
            if location.lower() in text_lower:
                return location, zip_code
        return None, None
    
    def search_posts(self, query, limit=50):
        print(f"Searching: {query}")
        posts_collected = 0
        try:
            response = self.client.app.bsky.feed.search_posts({'q': query, 'limit': limit})
            for post_view in response.posts:
                post = post_view.record
                author = post_view.author
                likes = post_view.like_count if hasattr(post_view, 'like_count') else 0
                reposts = post_view.repost_count if hasattr(post_view, 'repost_count') else 0
                replies = post_view.reply_count if hasattr(post_view, 'reply_count') else 0
                location, zip_code = self.extract_location(post.text)
                db_post = SocialMediaPost(
                    post_id=f"bluesky_{post_view.uri.split('/')[-1]}",
                    platform='bluesky',
                    author_id=author.did,
                    author_username=author.handle,
                    content=post.text,
                    timestamp=datetime.fromisoformat(post.created_at.replace('Z', '+00:00')),
                    url=f"https://bsky.app/profile/{author.handle}/post/{post_view.uri.split('/')[-1]}",
                    likes=likes, shares=reposts, comments=replies,
                    engagement_score=likes + (reposts * 3) + (replies * 2),
                    location_text=location, zip_code=zip_code, inferred_location=True if location else False,
                    raw_data={'uri': post_view.uri, 'author_display_name': author.display_name},
                    processed=False
                )
                existing = self.db_session.query(SocialMediaPost).filter_by(post_id=db_post.post_id).first()
                if not existing:
                    self.db_session.add(db_post)
                    posts_collected += 1
            self.db_session.commit()
            print(f"Collected {posts_collected} posts for: {query}")
            return posts_collected
        except Exception as e:
            print(f"Error: {e}")
            return 0
    
    def collect_all(self):
        total = 0
        for term in self.search_terms:
            try:
                count = self.search_posts(term, limit=25)
                total += count
            except Exception as e:
                print(f"Error for '{term}': {e}")
        print(f"Total: {total} posts")
        return total
    
    def close(self):
        self.db_session.close()

def main():
    print("Starting Bluesky collection...")
    collector = BlueskyCollector()
    try:
        total = collector.collect_all()
        return {'status': 'success', 'posts_collected': total, 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    finally:
        collector.close()

def bluesky_collector_function(request):
    return main()

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
