"""
Bluesky Data Collector for VA-11 Intelligence Platform
Collects posts from Bluesky using AT Protocol
"""
from atproto import Client
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from database.models import SocialMediaPost, get_connection_string, init_db
import json
import re


class BlueskCollector:
    def __init__(self):
        """Initialize Bluesky client"""
        self.client = Client()
        self.client.login(
            os.getenv('BLUESKY_HANDLE'),
            os.getenv('BLUESKY_PASSWORD')
        )
        
        # VA-11 relevant search terms
        self.search_terms = [
            'VA-11', 'Virginia 11th', 'Virginia House',
            'Fairfax County', 'Reston', 'Herndon', 'Vienna',
            'Walkinshaw', 'Northern Virginia politics'
        ]
        
        # Initialize database
        engine = init_db(get_connection_string())
        Session = sessionmaker(bind=engine)
        self.db_session = Session()
    
    def extract_location(self, text):
        """Try to extract location from text"""
        if not text:
            return None, None
        
        locations = {
            'Reston': '20190',
            'Herndon': '20170',
            'Vienna': '22180',
            'Oakton': '22124',
            'Great Falls': '22066',
            'McLean': '22101',
            'Tysons': '22102',
            'Fairfax': '22030'
        }
        
        text_lower = text.lower()
        for location, zip_code in locations.items():
            if location.lower() in text_lower:
                return location, zip_code
        
        return None, None
    
    def search_posts(self, query, limit=50):
        """Search for posts with a specific query"""
        print(f"Searching Bluesky for: {query}")
        posts_collected = 0
        
        try:
            # Search using AT Protocol
            response = self.client.app.bsky.feed.search_posts({
                'q': query,
                'limit': limit
            })
            
            for post_view in response.posts:
                post = post_view.record
                author = post_view.author
                
                # Extract engagement metrics
                likes = post_view.like_count if hasattr(post_view, 'like_count') else 0
                reposts = post_view.repost_count if hasattr(post_view, 'repost_count') else 0
                replies = post_view.reply_count if hasattr(post_view, 'reply_count') else 0
                
                # Extract location from text
                location, zip_code = self.extract_location(post.text)
                
                # Create post object
                db_post = SocialMediaPost(
                    post_id=f"bluesky_{post_view.uri.split('/')[-1]}",
                    platform='bluesky',
                    author_id=author.did,
                    author_username=author.handle,
                    content=post.text,
                    timestamp=datetime.fromisoformat(post.created_at.replace('Z', '+00:00')),
                    url=f"https://bsky.app/profile/{author.handle}/post/{post_view.uri.split('/')[-1]}",
                    likes=likes,
                    shares=reposts,
                    comments=replies,
                    engagement_score=likes + (reposts * 3) + (replies * 2),
                    location_text=location,
                    zip_code=zip_code,
                    inferred_location=True if location else False,
                    raw_data={
                        'uri': post_view.uri,
                        'author_display_name': author.display_name,
                        'author_avatar': author.avatar if hasattr(author, 'avatar') else None,
                        'indexed_at': post_view.indexed_at if hasattr(post_view, 'indexed_at') else None,
                        'has_embed': hasattr(post, 'embed') and post.embed is not None,
                        'facets': post.facets if hasattr(post, 'facets') else None
                    },
                    processed=False
                )
                
                # Check if already exists
                existing = self.db_session.query(SocialMediaPost).filter_by(
                    post_id=db_post.post_id
                ).first()
                
                if not existing:
                    self.db_session.add(db_post)
                    posts_collected += 1
            
            self.db_session.commit()
            print(f"Collected {posts_collected} new posts for query: {query}")
            return posts_collected
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return 0
    
    def get_timeline_posts(self, limit=100):
        """Get posts from timeline/feed (alternative approach)"""
        print("Collecting from Bluesky timeline...")
        posts_collected = 0
        
        try:
            # Get timeline feed
            timeline = self.client.get_timeline(limit=limit)
            
            for feed_view in timeline.feed:
                post_view = feed_view.post
                post = post_view.record
                author = post_view.author
                
                # Check if VA-11 relevant
                text_lower = post.text.lower()
                is_relevant = any(
                    term.lower() in text_lower 
                    for term in self.search_terms
                )
                
                if not is_relevant:
                    continue
                
                # Extract engagement metrics
                likes = post_view.like_count if hasattr(post_view, 'like_count') else 0
                reposts = post_view.repost_count if hasattr(post_view, 'repost_count') else 0
                replies = post_view.reply_count if hasattr(post_view, 'reply_count') else 0
                
                # Extract location
                location, zip_code = self.extract_location(post.text)
                
                # Create post object
                db_post = SocialMediaPost(
                    post_id=f"bluesky_{post_view.uri.split('/')[-1]}",
                    platform='bluesky',
                    author_id=author.did,
                    author_username=author.handle,
                    content=post.text,
                    timestamp=datetime.fromisoformat(post.created_at.replace('Z', '+00:00')),
                    url=f"https://bsky.app/profile/{author.handle}/post/{post_view.uri.split('/')[-1]}",
                    likes=likes,
                    shares=reposts,
                    comments=replies,
                    engagement_score=likes + (reposts * 3) + (replies * 2),
                    location_text=location,
                    zip_code=zip_code,
                    inferred_location=True if location else False,
                    raw_data={
                        'uri': post_view.uri,
                        'author_display_name': author.display_name,
                        'from_timeline': True
                    },
                    processed=False
                )
                
                # Check if already exists
                existing = self.db_session.query(SocialMediaPost).filter_by(
                    post_id=db_post.post_id
                ).first()
                
                if not existing:
                    self.db_session.add(db_post)
                    posts_collected += 1
            
            self.db_session.commit()
            print(f"Collected {posts_collected} new posts from timeline")
            return posts_collected
            
        except Exception as e:
            print(f"Error getting timeline: {e}")
            return 0
    
    def collect_all(self):
        """Collect using all methods"""
        total_collected = 0
        
        # Method 1: Search for specific terms
        for term in self.search_terms:
            try:
                count = self.search_posts(term, limit=25)
                total_collected += count
            except Exception as e:
                print(f"Error searching for '{term}': {e}")
        
        # Method 2: Check timeline for relevant posts
        try:
            count = self.get_timeline_posts(limit=100)
            total_collected += count
        except Exception as e:
            print(f"Error getting timeline: {e}")
        
        print(f"\nTotal collected from Bluesky: {total_collected} posts")
        return total_collected
    
    def close(self):
        """Close database session"""
        self.db_session.close()


def main():
    """Main function for Cloud Function deployment"""
    print("Starting Bluesky collection...")
    collector = BlueskCollector()
    
    try:
        total = collector.collect_all()
        return {
            'status': 'success',
            'posts_collected': total,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error in Bluesky collection: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        collector.close()


# Cloud Function entry point
def bluesky_collector_function(request):
    """GCP Cloud Function entry point"""
    return main()


if __name__ == "__main__":
    # For local testing
    from dotenv import load_dotenv
    load_dotenv()
    result = main()
    print(json.dumps(result, indent=2))
