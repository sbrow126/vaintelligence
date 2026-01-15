"""Sentiment analyzer using GCP Natural Language API"""
from google.cloud import language_v1
import os
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('..')
from database.models import SocialMediaPost, SentimentAnalysis, Topic, PostTopic, get_connection_string, init_db
import json

class SentimentAnalyzer:
    def __init__(self):
        self.client = language_v1.LanguageServiceClient()
        engine = init_db(get_connection_string())
        Session = sessionmaker(bind=engine)
        self.db_session = Session()
        self.initialize_topics()
    
    def initialize_topics(self):
        topics_config = [
            {'name': 'Housing & Affordability', 'category': 'housing', 'keywords': ['housing', 'rent', 'mortgage', 'affordability', 'zoning']},
            {'name': 'Transportation', 'category': 'transportation', 'keywords': ['traffic', 'metro', 'road', 'route 7', 'silver line']},
            {'name': 'Education', 'category': 'education', 'keywords': ['school', 'education', 'teacher', 'fcps', 'student']},
            {'name': 'Healthcare', 'category': 'healthcare', 'keywords': ['healthcare', 'hospital', 'insurance', 'medicaid']},
            {'name': 'Public Safety', 'category': 'safety', 'keywords': ['police', 'fire', 'safety', 'crime', 'emergency']},
            {'name': 'Environment', 'category': 'environment', 'keywords': ['climate', 'environment', 'pollution', 'green', 'sustainability']},
            {'name': 'Economy & Jobs', 'category': 'economy', 'keywords': ['jobs', 'employment', 'economy', 'business', 'wages']},
            {'name': 'Social Infrastructure', 'category': 'social', 'keywords': ['community center', 'library', 'parks', 'recreation']},
            {'name': 'LGBTQ+ Rights', 'category': 'rights', 'keywords': ['lgbtq', 'gay', 'lesbian', 'transgender', 'pride']},
            {'name': 'Immigration', 'category': 'immigration', 'keywords': ['immigrant', 'immigration', 'visa', 'citizenship', 'ice']},
            {'name': 'Taxes & Budget', 'category': 'fiscal', 'keywords': ['tax', 'budget', 'revenue', 'spending', 'fiscal']},
            {'name': 'Federal Workforce', 'category': 'employment', 'keywords': ['federal worker', 'government employee', 'civil servant', 'doge']}
        ]
        for config in topics_config:
            existing = self.db_session.query(Topic).filter_by(name=config['name']).first()
            if not existing:
                topic = Topic(name=config['name'], category=config['category'], keywords=config['keywords'], active=True)
                self.db_session.add(topic)
        self.db_session.commit()
    
    def analyze_sentiment(self, text):
        if not text or len(text.strip()) < 10: return None
        if len(text) > 5000: text = text[:5000]
        try:
            document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
            sentiment = self.client.analyze_sentiment(request={'document': document}).document_sentiment
            entities_response = self.client.analyze_entities(request={'document': document})
            entities = [{'name': entity.name, 'type': language_v1.Entity.Type(entity.type_).name, 'salience': entity.salience} for entity in entities_response.entities]
            try:
                categories_response = self.client.classify_text(request={'document': document})
                categories = [{'name': cat.name, 'confidence': cat.confidence} for cat in categories_response.categories]
            except: categories = []
            return {'sentiment_score': sentiment.score, 'sentiment_magnitude': sentiment.magnitude, 'entities': entities, 'categories': categories}
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def categorize_sentiment(self, score):
        if score >= 0.25: return 'positive'
        elif score <= -0.25: return 'negative'
        else: return 'neutral'
    
    def match_topics(self, text, entities):
        text_lower = text.lower()
        matched_topics = []
        topics = self.db_session.query(Topic).filter_by(active=True).all()
        for topic in topics:
            relevance_score = 0.0
            for keyword in topic.keywords:
                if keyword.lower() in text_lower: relevance_score += 0.2
            for entity in entities:
                for keyword in topic.keywords:
                    if keyword.lower() in entity['name'].lower(): relevance_score += entity['salience'] * 0.5
            if relevance_score > 0.1:
                matched_topics.append({'topic_id': topic.topic_id, 'relevance_score': min(relevance_score, 1.0)})
        return matched_topics
    
    def process_post(self, post):
        existing = self.db_session.query(SentimentAnalysis).filter_by(post_id=post.post_id).first()
        if existing: return False
        analysis_result = self.analyze_sentiment(post.content)
        if not analysis_result: return False
        sentiment = SentimentAnalysis(
            post_id=post.post_id,
            sentiment_score=analysis_result['sentiment_score'],
            sentiment_magnitude=analysis_result['sentiment_magnitude'],
            sentiment_category=self.categorize_sentiment(analysis_result['sentiment_score']),
            confidence=1.0,
            entities=analysis_result['entities'],
            categories=analysis_result['categories'],
            analyzed_at=datetime.utcnow(),
            model_version='gcp_natural_language_v1'
        )
        self.db_session.add(sentiment)
        matched_topics = self.match_topics(post.content, analysis_result['entities'])
        for topic_match in matched_topics:
            post_topic = PostTopic(post_id=post.post_id, topic_id=topic_match['topic_id'], relevance_score=topic_match['relevance_score'])
            self.db_session.add(post_topic)
        post.processed = True
        return True
    
    def process_unanalyzed_posts(self, limit=100):
        unanalyzed = self.db_session.query(SocialMediaPost).filter_by(processed=False).limit(limit).all()
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
        print(f"Total processed: {processed_count}")
        return processed_count
    
    def close(self):
        self.db_session.close()

def main():
    print("Starting sentiment analysis...")
    analyzer = SentimentAnalyzer()
    try:
        count = analyzer.process_unanalyzed_posts(limit=200)
        return {'status': 'success', 'posts_processed': count, 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    finally:
        analyzer.close()

def sentiment_analyzer_function(request):
    return main()

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
