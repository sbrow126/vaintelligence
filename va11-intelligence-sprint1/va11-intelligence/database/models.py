"""
Database models for VA-11 Constituent Intelligence Platform
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os

Base = declarative_base()


class SocialMediaPost(Base):
    """Raw social media posts from all platforms"""
    __tablename__ = 'social_media_posts'
    
    post_id = Column(String(255), primary_key=True)
    platform = Column(String(50), nullable=False, index=True)  # reddit, bluesky, etc.
    author_id = Column(String(255))
    author_username = Column(String(255))
    content = Column(Text)
    timestamp = Column(DateTime, nullable=False, index=True)
    url = Column(String(500))
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    
    # Location data
    location_text = Column(String(255))  # "Reston, VA", "Fairfax County"
    zip_code = Column(String(10))
    inferred_location = Column(Boolean, default=False)
    
    # Metadata
    raw_data = Column(JSON)  # Store complete API response
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sentiment = relationship("SentimentAnalysis", back_populates="post", uselist=False)
    topics = relationship("PostTopic", back_populates="post")


class SentimentAnalysis(Base):
    """Sentiment analysis results from GCP Natural Language API"""
    __tablename__ = 'sentiment_analysis'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), ForeignKey('social_media_posts.post_id'), unique=True)
    
    # Sentiment scores
    sentiment_score = Column(Float)  # -1.0 (negative) to 1.0 (positive)
    sentiment_magnitude = Column(Float)  # Overall strength of emotion
    sentiment_category = Column(String(20))  # positive, negative, neutral
    confidence = Column(Float)
    
    # Entity and topic extraction
    entities = Column(JSON)  # List of entities mentioned
    categories = Column(JSON)  # Content categories
    
    # Analysis metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))
    
    # Relationships
    post = relationship("SocialMediaPost", back_populates="sentiment")


class Topic(Base):
    """Issue topics/categories"""
    __tablename__ = 'topics'
    
    topic_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # housing, education, transportation, etc.
    keywords = Column(JSON)  # List of keywords for matching
    description = Column(Text)
    active = Column(Boolean, default=True)
    
    # Relationships
    posts = relationship("PostTopic", back_populates="topic")


class PostTopic(Base):
    """Many-to-many relationship between posts and topics"""
    __tablename__ = 'post_topics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), ForeignKey('social_media_posts.post_id'))
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    relevance_score = Column(Float)  # How relevant is this topic to the post
    
    # Relationships
    post = relationship("SocialMediaPost", back_populates="topics")
    topic = relationship("Topic", back_populates="posts")


class Influencer(Base):
    """Key voices in the district"""
    __tablename__ = 'influencers'
    
    user_id = Column(String(255), primary_key=True)
    platform = Column(String(50), nullable=False)
    username = Column(String(255))
    display_name = Column(String(255))
    
    # Metrics
    follower_count = Column(Integer)
    avg_engagement_rate = Column(Float)
    total_posts = Column(Integer, default=0)
    total_engagement = Column(Integer, default=0)
    
    # Topics they discuss
    primary_topics = Column(JSON)
    topic_expertise = Column(JSON)  # {topic_id: expertise_score}
    
    # Status
    influence_score = Column(Float)  # Calculated overall influence
    last_active = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    profile_data = Column(JSON)


class TrendTracking(Base):
    """Track trends over time"""
    __tablename__ = 'trend_tracking'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    date = Column(DateTime, nullable=False, index=True)
    
    # Metrics for this topic on this date
    mention_count = Column(Integer, default=0)
    sentiment_average = Column(Float)
    engagement_total = Column(Integer, default=0)
    
    # Velocity calculations
    velocity = Column(Float)  # Rate of change from previous period
    acceleration = Column(Float)  # Change in velocity
    
    # Alert status
    alert_level = Column(String(20))  # none, low, medium, high
    
    topic = relationship("Topic")


class Alert(Base):
    """System-generated alerts"""
    __tablename__ = 'alerts'
    
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)  # early_warning, misinformation, spike, etc.
    severity = Column(String(20))  # low, medium, high, critical
    
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    title = Column(String(255))
    description = Column(Text)
    
    # Alert data
    trigger_data = Column(JSON)  # What triggered this alert
    recommended_action = Column(Text)
    
    # Status
    status = Column(String(20), default='active')  # active, acknowledged, resolved
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    topic = relationship("Topic")


class Demographics(Base):
    """Census demographics by zip code"""
    __tablename__ = 'demographics'
    
    zip_code = Column(String(10), primary_key=True)
    
    # Population
    total_population = Column(Integer)
    population_density = Column(Float)
    
    # Age distribution (percentages)
    age_distribution = Column(JSON)  # {"18-24": 15.2, "25-34": 22.1, ...}
    median_age = Column(Float)
    
    # Household composition
    single_person_households = Column(Float)  # percentage
    family_households = Column(Float)
    households_with_children = Column(Float)
    
    # Economic
    median_income = Column(Integer)
    income_distribution = Column(JSON)
    
    # Race/Ethnicity
    race_distribution = Column(JSON)
    
    # Other
    education_level = Column(JSON)
    employment_status = Column(JSON)
    
    # Metadata
    data_year = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)


class GeographicActivity(Base):
    """Link posts to geographic areas"""
    __tablename__ = 'geographic_activity'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), ForeignKey('social_media_posts.post_id'))
    zip_code = Column(String(10), ForeignKey('demographics.zip_code'))
    
    confidence = Column(Float)  # How confident are we in this location
    inferred = Column(Boolean, default=False)  # Was location explicitly stated or inferred
    
    post = relationship("SocialMediaPost")
    demographics = relationship("Demographics")


class LegislativeActivity(Base):
    """Track James Walkinshaw's legislative activity"""
    __tablename__ = 'legislative_activity'
    
    bill_id = Column(String(50), primary_key=True)
    session_year = Column(Integer, nullable=False)
    bill_number = Column(String(50), nullable=False)
    
    title = Column(String(500))
    summary = Column(Text)
    full_text_url = Column(String(500))
    
    # Walkinshaw's involvement
    walkinshaw_role = Column(String(50))  # sponsor, co-sponsor, voted
    walkinshaw_position = Column(String(20))  # yes, no, abstain
    vote_date = Column(DateTime)
    
    # Bill status
    status = Column(String(50))
    committee = Column(String(255))
    
    # Topics
    primary_topic = Column(String(100))
    tags = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class LegislativeSentiment(Base):
    """Track constituent sentiment about legislative activity"""
    __tablename__ = 'legislative_sentiment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(String(50), ForeignKey('legislative_activity.bill_id'))
    date = Column(DateTime, nullable=False, index=True)
    
    # Metrics
    mention_count = Column(Integer, default=0)
    sentiment_average = Column(Float)
    awareness_score = Column(Float)  # What % of district discussions mention this
    
    # Support breakdown
    support_percentage = Column(Float)
    oppose_percentage = Column(Float)
    neutral_percentage = Column(Float)
    
    bill = relationship("LegislativeActivity")


# Database initialization function
def init_db(connection_string):
    """Initialize database with all tables"""
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return engine


def get_connection_string():
    """Build connection string from environment variables"""
    return f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"


if __name__ == "__main__":
    # Initialize database
    conn_string = get_connection_string()
    engine = init_db(conn_string)
    print("Database initialized successfully!")
