"""
Reddit Data Collector for VA-11 Intelligence Platform
Collects posts and comments from relevant subreddits
"""
import praw
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from database.models import SocialMediaPost, get_connection_string, init_db
import json
import re


class RedditCollector:
    def __init__(self):
        """Initialize Reddit API client"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        
        # VA-11 relevant subreddits
        self.subreddits = ['nova', 'fairfaxcounty', 'reston', 'Virginia', 'nova_politics']
        
        # Keywords to filter for VA-11 relevance
        self.keywords = [
            'VA-11', 'Virginia 11', 'Virginia 11th',
            'Fairfax County', 'Reston', 'Herndon', 'Vienna', 
            'Oakton', 'Great Falls', 'McLean', 'Tysons',
            'Walkinshaw', 'VA House', 'Virginia House'
        ]
        
        # Initialize database
        engine = init_db(get_connection_string())
        Session = sessionmaker(bind=engine)
        self.db_session = Session()
    
    def is_va11_relevant(self, text):
        """Check if text is relevant to VA-11"""
        if not text:
            return False
        
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def extract_location(self, text):
        """Try to extract location from text"""
        if not text:
            return None, None
        
        # Simple pattern matching for locations
        locations = {
            'Reston': '20190',
            'Herndon': '20170',
            'Vienna': '22180',
            'Oakton': '22124',
            'Great Falls': '22066',
            'McLean': '22101',
            'Tysons': '22102'
        }
        
        text_lower = text.lower()
        for location, zip_code in locations.items():
            if location.lower() in text_lower:
                return location, zip_code
        
        return None, None
    
    def collect_subreddit_posts(self, subreddit_name, limit=100, time_filter='week'):
        """Collect recent posts from a subreddit"""
        print(f"Collecting from r/{subreddit_name}...")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts_collected = 0
        
        # Get hot and new posts
        for submission in subreddit.hot(limit=limit):
            # Check relevance
            full_text = f"{submission.title} {submission.selftext}"
            if not self.is_va11_relevant(full_text):
                continue
            
            # Extract location
            location, zip_code = self.extract_location(full_text)
            
            # Create post object
            post = SocialMediaPost(
                post_id=f"reddit_{submission.id}",
                platform='reddit',
                author_id=str(submission.author) if submission.author else '[deleted]',
                author_username=str(submission.author) if submission.author else '[deleted]',
                content=f"{submission.title}\n\n{submission.selftext}",
                timestamp=datetime.fromtimestamp(submission.created_utc),
                url=f"https://reddit.com{submission.permalink}",
                likes=submission.score,
                comments=submission.num_comments,
                engagement_score=submission.score + (submission.num_comments * 2),
                location_text=location,
                zip_code=zip_code,
                inferred_location=True if location else False,
                raw_data={
                    'subreddit': subreddit_name,
                    'link_flair_text': submission.link_flair_text,
                    'upvote_ratio': submission.upvote_ratio,
                    'awards': submission.total_awards_received,
                    'is_self': submission.is_self
                },
                processed=False
            )
            
            # Check if already exists
            existing = self.db_session.query(SocialMediaPost).filter_by(
                post_id=post.post_id
            ).first()
            
            if not existing:
                self.db_session.add(post)
                posts_collected += 1
            
            # Also collect top comments
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:5]:  # Top 5 comments
                if not self.is_va11_relevant(comment.body):
                    continue
                
                comment_location, comment_zip = self.extract_location(comment.body)
                
                comment_post = SocialMediaPost(
                    post_id=f"reddit_{comment.id}",
                    platform='reddit',
                    author_id=str(comment.author) if comment.author else '[deleted]',
                    author_username=str(comment.author) if comment.author else '[deleted]',
                    content=comment.body,
                    timestamp=datetime.fromtimestamp(comment.created_utc),
                    url=f"https://reddit.com{comment.permalink}",
                    likes=comment.score,
                    comments=0,
                    engagement_score=comment.score,
                    location_text=comment_location,
                    zip_code=comment_zip,
                    inferred_location=True if comment_location else False,
                    raw_data={
                        'parent_id': submission.id,
                        'subreddit': subreddit_name,
                        'is_comment': True
                    },
                    processed=False
                )
                
                existing_comment = self.db_session.query(SocialMediaPost).filter_by(
                    post_id=comment_post.post_id
                ).first()
                
                if not existing_comment:
                    self.db_session.add(comment_post)
                    posts_collected += 1
        
        self.db_session.commit()
        print(f"Collected {posts_collected} new posts/comments from r/{subreddit_name}")
        return posts_collected
    
    def collect_all(self):
        """Collect from all configured subreddits"""
        total_collected = 0
        for subreddit in self.subreddits:
            try:
                count = self.collect_subreddit_posts(subreddit)
                total_collected += count
            except Exception as e:
                print(f"Error collecting from r/{subreddit}: {e}")
        
        print(f"\nTotal collected: {total_collected} posts/comments")
        return total_collected
    
    def close(self):
        """Close database session"""
        self.db_session.close()


def main():
    """Main function for Cloud Function deployment"""
    print("Starting Reddit collection...")
    collector = RedditCollector()
    
    try:
        total = collector.collect_all()
        return {
            'status': 'success',
            'posts_collected': total,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error in Reddit collection: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        collector.close()


# Cloud Function entry point
def reddit_collector_function(request):
    """GCP Cloud Function entry point"""
    return main()


if __name__ == "__main__":
    # For local testing
    from dotenv import load_dotenv
    load_dotenv()
    result = main()
    print(json.dumps(result, indent=2))
