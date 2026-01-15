"""Database models for VA-11 Platform"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os

Base = declarative_base()

class SocialMediaPost(Base):
    __tablename__ = 'social_media_posts'
    post_id = Column(String(255), primary_key=True)
    platform = Column(String(50), nullable=False, index=True)
    author_id = Column(String(255))
    author_username = Column(String(255))
    content = Column(Text)
    timestamp = Column(DateTime, nullable=False, index=True)
    url = Column(String(500))
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    location_text = Column(String(255))
    zip_code = Column(String(10))
    inferred_location = Column(Boolean, default=False)
    raw_data = Column(JSON)
    processed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sentiment = relationship("SentimentAnalysis", back_populates="post", uselist=False)
    topics = relationship("PostTopic", back_populates="post")

class SentimentAnalysis(Base):
    __tablename__ = 'sentiment_analysis'
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), ForeignKey('social_media_posts.post_id'), unique=True)
    sentiment_score = Column(Float)
    sentiment_magnitude = Column(Float)
    sentiment_category = Column(String(20))
    confidence = Column(Float)
    entities = Column(JSON)
    categories = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))
    post = relationship("SocialMediaPost", back_populates="sentiment")

class Topic(Base):
    __tablename__ = 'topics'
    topic_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    keywords = Column(JSON)
    description = Column(Text)
    active = Column(Boolean, default=True)
    posts = relationship("PostTopic", back_populates="topic")

class PostTopic(Base):
    __tablename__ = 'post_topics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(255), ForeignKey('social_media_posts.post_id'))
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    relevance_score = Column(Float)
    post = relationship("SocialMediaPost", back_populates="topics")
    topic = relationship("Topic", back_populates="posts")

def get_connection_string():
    db_host = os.getenv('DB_HOST', '/cloudsql/' + os.getenv('CLOUD_SQL_CONNECTION_NAME', 'va11-intelligence:us-east4:va11-db'))
    db_name = os.getenv('DB_NAME', 'va11_intelligence')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    if '/cloudsql/' in db_host:
        return f"postgresql://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        db_port = os.getenv('DB_PORT', '5432')
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def init_db(connection_string):
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return engine
