"""
Sentiment Analysis using GCP Natural Language API
Processes unanalyzed posts and extracts sentiment, entities, and topics
"""
from google.cloud import language_v1
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from database.models import (
    SocialMediaPost, SentimentAnalysis, Topic, PostTopic,
    get_connection_string, init_db
)
import json


class SentimentAnalyzer:
    def __init__(self):
        """Initialize GCP Natural Language API client"""
        self.client = language_v1.LanguageServiceClient()
        
        # Initialize database
        engine = init_db(get_connection_string())
        Session = sessionmaker(bind=engine)
        self.db_session = Session()
        
        # Initialize topics if they don't exist
        self.initialize_topics()
    
    def initialize_topics(self):
        """Create predefined topics if they don't exist"""
        topics_config = [
            {
                'name': 'Housing & Affordability',
                'category': 'housing',
                'keywords': ['housing', 'rent', 'mortgage', 'affordability', 'apartment', 'homeowner', 'zoning', 'development']
            },
            {
                'name': 'Transportation & Infrastructure',
                'category': 'transportation',
                'keywords': ['traffic', 'metro', 'road', 'route 7', 'dulles', 'silver line', 'bike lane', 'pedestrian', 'infrastructure']
            },
            {
                'name': 'Education & Schools',
                'category': 'education',
                'keywords': ['school', 'education', 'teacher', 'fcps', 'classroom', 'student', 'college', 'university']
            },
            {
                'name': 'Healthcare',
                'category': 'healthcare',
                'keywords': ['healthcare', 'hospital', 'insurance', 'medicaid', 'doctor', 'medical', 'health']
            },
            {
                'name': 'Public Safety',
                'category': 'safety',
                'keywords': ['police', 'fire', 'safety', 'crime', 'emergency', 'security']
            },
            {
                'name': 'Environment & Climate',
                'category': 'environment',
                'keywords': ['climate', 'environment', 'pollution', 'green', 'sustainability', 'clean energy', 'solar']
            },
            {
                'name': 'Economy & Jobs',
                'category': 'economy',
                'keywords': ['jobs', 'employment', 'economy', 'business', 'unemployment', 'wages', 'workforce']
            },
            {
                'name': 'Social Infrastructure',
                'category': 'social',
                'keywords': ['community center', 'library', 'parks', 'recreation', 'third space', 'gathering', 'social']
            },
            {
                'name': 'LGBTQ+ Rights',
                'category': 'rights',
                'keywords': ['lgbtq', 'gay', 'lesbian', 'transgender', 'pride', 'equality', 'discrimination']
            },
            {
                'name': 'Immigration',
                'category': 'immigration',
                'keywords': ['immigrant', 'immigration', 'visa', 'citizenship', 'undocumented', 'refugee', 'ice']
            },
            {
                'name': 'Taxes & Budget',
                'category': 'fiscal',
                'keywords': ['tax', 'budget', 'revenue', 'spending', 'fiscal', 'property tax']
            },
            {
                'name': 'Federal Workforce',
                'category': 'employment',
                'keywords': ['federal worker', 'government employee', 'civil servant', 'federal job', 'doge', 'usajobs']
            }
        ]
        
        for topic_config in topics_config:
            existing = self.db_session.query(Topic).filter_by(name=topic_config['name']).first()
            if not existing:
                topic = Topic(
                    name=topic_config['name'],
                    category=topic_config['category'],
                    keywords=topic_config['keywords'],
                    active=True
                )
                self.db_session.add(topic)
        
        self.db_session.commit()
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using GCP Natural Language API"""
        if not text or len(text.strip()) < 10:
            return None
        
        # Truncate if too long (GCP has limits)
        if len(text) > 5000:
            text = text[:5000]
        
        try:
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            # Get sentiment
            sentiment = self.client.analyze_sentiment(
                request={'document': document}
            ).document_sentiment
            
            # Get entities
            entities_response = self.client.analyze_entities(
                request={'document': document}
            )
            
            # Extract entity information
            entities = []
            for entity in entities_response.entities:
                entities.append({
                    'name': entity.name,
                    'type': language_v1.Entity.Type(entity.type_).name,
                    'salience': entity.salience,
                    'sentiment_score': entity.sentiment.score if hasattr(entity, 'sentiment') else None
                })
            
            # Get content categories
            try:
                categories_response = self.client.classify_text(
                    request={'document': document}
                )
                categories = [
                    {'name': category.name, 'confidence': category.confidence}
                    for category in categories_response.categories
                ]
            except:
                categories = []
            
            return {
                'sentiment_score': sentiment.score,
                'sentiment_magnitude': sentiment.magnitude,
                'entities': entities,
                'categories': categories
            }
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return None
    
    def categorize_sentiment(self, score):
        """Convert score to category"""
        if score >= 0.25:
            return 'positive'
        elif score <= -0.25:
            return 'negative'
        else:
            return 'neutral'
    
    def match_topics(self, text, entities):
        """Match post to topics based on keywords and entities"""
        text_lower = text.lower()
        matched_topics = []
        
        # Get all active topics
        topics = self.db_session.query(Topic).filter_by(active=True).all()
        
        for topic in topics:
            relevance_score = 0.0
            
            # Check keywords
            for keyword in topic.keywords:
                if keyword.lower() in text_lower:
                    relevance_score += 0.2
            
            # Check entities
            for entity in entities:
                entity_name_lower = entity['name'].lower()
                for keyword in topic.keywords:
                    if keyword.lower() in entity_name_lower:
                        relevance_score += entity['salience'] * 0.5
            
            if relevance_score > 0.1:  # Threshold for relevance
                matched_topics.append({
                    'topic_id': topic.topic_id,
                    'relevance_score': min(relevance_score, 1.0)  # Cap at 1.0
                })
        
        return matched_topics
    
    def process_post(self, post):
        """Process a single post for sentiment and topics"""
        # Check if already analyzed
        existing = self.db_session.query(SentimentAnalysis).filter_by(
            post_id=post.post_id
        ).first()
        
        if existing:
            return False  # Already processed
        
        # Analyze sentiment
        analysis_result = self.analyze_sentiment(post.content)
        
        if not analysis_result:
            return False
        
        # Create sentiment analysis record
        sentiment = SentimentAnalysis(
            post_id=post.post_id,
            sentiment_score=analysis_result['sentiment_score'],
            sentiment_magnitude=analysis_result['sentiment_magnitude'],
            sentiment_category=self.categorize_sentiment(analysis_result['sentiment_score']),
            confidence=1.0,  # GCP doesn't provide confidence, but we trust it
            entities=analysis_result['entities'],
            categories=analysis_result['categories'],
            analyzed_at=datetime.utcnow(),
            model_version='gcp_natural_language_v1'
        )
        
        self.db_session.add(sentiment)
        
        # Match topics
        matched_topics = self.match_topics(
            post.content,
            analysis_result['entities']
        )
        
        for topic_match in matched_topics:
            post_topic = PostTopic(
                post_id=post.post_id,
                topic_id=topic_match['topic_id'],
                relevance_score=topic_match['relevance_score']
            )
            self.db_session.add(post_topic)
        
        # Mark post as processed
        post.processed = True
        
        return True
    
    def process_unanalyzed_posts(self, limit=100):
        """Process all unanalyzed posts"""
        unanalyzed = self.db_session.query(SocialMediaPost).filter_by(
            processed=False
        ).limit(limit).all()
        
        processed_count = 0
        for post in unanalyzed:
            try:
                if self.process_post(post):
                    processed_count += 1
                    if processed_count % 10 == 0:
                        self.db_session.commit()
                        print(f"Processed {processed_count} posts...")
            except Exception as e:
                print(f"Error processing post {post.post_id}: {e}")
        
        self.db_session.commit()
        print(f"Total processed: {processed_count} posts")
        return processed_count
    
    def close(self):
        """Close database session"""
        self.db_session.close()


def main():
    """Main function for Cloud Function deployment"""
    print("Starting sentiment analysis...")
    analyzer = SentimentAnalyzer()
    
    try:
        count = analyzer.process_unanalyzed_posts(limit=200)
        return {
            'status': 'success',
            'posts_processed': count,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        analyzer.close()


# Cloud Function entry point
def sentiment_analyzer_function(request):
    """GCP Cloud Function entry point"""
    return main()


if __name__ == "__main__":
    # For local testing
    from dotenv import load_dotenv
    load_dotenv()
    result = main()
    print(json.dumps(result, indent=2))
