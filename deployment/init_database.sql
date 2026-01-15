-- VA-11 Intelligence Platform Database Schema
-- Run this in Cloud SQL to create all tables

-- Social media posts table
CREATE TABLE social_media_posts (
    post_id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    author_id VARCHAR(255),
    author_username VARCHAR(255),
    content TEXT,
    timestamp TIMESTAMP NOT NULL,
    url VARCHAR(500),
    
    -- Engagement metrics
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    engagement_score FLOAT DEFAULT 0.0,
    
    -- Location data
    location_text VARCHAR(255),
    zip_code VARCHAR(10),
    inferred_location BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    raw_data JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_timestamp ON social_media_posts(timestamp);
CREATE INDEX idx_posts_platform ON social_media_posts(platform);
CREATE INDEX idx_posts_processed ON social_media_posts(processed);

-- Sentiment analysis table
CREATE TABLE sentiment_analysis (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(255) UNIQUE REFERENCES social_media_posts(post_id),
    
    -- Sentiment scores
    sentiment_score FLOAT,
    sentiment_magnitude FLOAT,
    sentiment_category VARCHAR(20),
    confidence FLOAT,
    
    -- Entity and topic extraction
    entities JSONB,
    categories JSONB,
    
    -- Analysis metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50)
);

CREATE INDEX idx_sentiment_post ON sentiment_analysis(post_id);

-- Topics table
CREATE TABLE topics (
    topic_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    keywords JSONB,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Insert predefined topics
INSERT INTO topics (name, category, keywords, description) VALUES
('Housing & Affordability', 'housing', '["housing", "rent", "mortgage", "affordability", "apartment", "homeowner", "zoning", "development"]', 'Housing costs and availability'),
('Transportation & Infrastructure', 'transportation', '["traffic", "metro", "road", "route 7", "dulles", "silver line", "bike lane", "pedestrian", "infrastructure"]', 'Transportation and roads'),
('Education & Schools', 'education', '["school", "education", "teacher", "fcps", "classroom", "student", "college", "university"]', 'Schools and education'),
('Healthcare', 'healthcare', '["healthcare", "hospital", "insurance", "medicaid", "doctor", "medical", "health"]', 'Healthcare access and costs'),
('Public Safety', 'safety', '["police", "fire", "safety", "crime", "emergency", "security"]', 'Public safety and emergency services'),
('Environment & Climate', 'environment', '["climate", "environment", "pollution", "green", "sustainability", "clean energy", "solar"]', 'Environmental issues'),
('Economy & Jobs', 'economy', '["jobs", "employment", "economy", "business", "unemployment", "wages", "workforce"]', 'Economic and employment issues'),
('Social Infrastructure', 'social', '["community center", "library", "parks", "recreation", "third space", "gathering", "social"]', 'Community spaces and social infrastructure'),
('LGBTQ+ Rights', 'rights', '["lgbtq", "gay", "lesbian", "transgender", "pride", "equality", "discrimination"]', 'LGBTQ+ rights and issues'),
('Immigration', 'immigration', '["immigrant", "immigration", "visa", "citizenship", "undocumented", "refugee", "ice"]', 'Immigration policy'),
('Taxes & Budget', 'fiscal', '["tax", "budget", "revenue", "spending", "fiscal", "property tax"]', 'Taxes and government spending'),
('Federal Workforce', 'employment', '["federal worker", "government employee", "civil servant", "federal job", "doge", "usajobs"]', 'Federal workforce issues');

-- Post topics junction table
CREATE TABLE post_topics (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(255) REFERENCES social_media_posts(post_id),
    topic_id INTEGER REFERENCES topics(topic_id),
    relevance_score FLOAT
);

CREATE INDEX idx_post_topics_post ON post_topics(post_id);
CREATE INDEX idx_post_topics_topic ON post_topics(topic_id);

-- Influencers table
CREATE TABLE influencers (
    user_id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(255),
    display_name VARCHAR(255),
    
    -- Metrics
    follower_count INTEGER,
    avg_engagement_rate FLOAT,
    total_posts INTEGER DEFAULT 0,
    total_engagement INTEGER DEFAULT 0,
    
    -- Topics
    primary_topics JSONB,
    topic_expertise JSONB,
    
    -- Status
    influence_score FLOAT,
    last_active TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    profile_data JSONB
);

-- Trend tracking table
CREATE TABLE trend_tracking (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(topic_id),
    date TIMESTAMP NOT NULL,
    
    -- Metrics
    mention_count INTEGER DEFAULT 0,
    sentiment_average FLOAT,
    engagement_total INTEGER DEFAULT 0,
    
    -- Velocity
    velocity FLOAT,
    acceleration FLOAT,
    
    -- Alert status
    alert_level VARCHAR(20)
);

CREATE INDEX idx_trends_date ON trend_tracking(date);
CREATE INDEX idx_trends_topic ON trend_tracking(topic_id);

-- Alerts table
CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),
    
    topic_id INTEGER REFERENCES topics(topic_id),
    title VARCHAR(255),
    description TEXT,
    
    -- Alert data
    trigger_data JSONB,
    recommended_action TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_alerts_created ON alerts(created_at);
CREATE INDEX idx_alerts_status ON alerts(status);

-- Demographics table
CREATE TABLE demographics (
    zip_code VARCHAR(10) PRIMARY KEY,
    
    -- Population
    total_population INTEGER,
    population_density FLOAT,
    
    -- Age distribution
    age_distribution JSONB,
    median_age FLOAT,
    
    -- Household composition
    single_person_households FLOAT,
    family_households FLOAT,
    households_with_children FLOAT,
    
    -- Economic
    median_income INTEGER,
    income_distribution JSONB,
    
    -- Race/Ethnicity
    race_distribution JSONB,
    
    -- Other
    education_level JSONB,
    employment_status JSONB,
    
    -- Metadata
    data_year INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Geographic activity table
CREATE TABLE geographic_activity (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(255) REFERENCES social_media_posts(post_id),
    zip_code VARCHAR(10) REFERENCES demographics(zip_code),
    
    confidence FLOAT,
    inferred BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_geo_post ON geographic_activity(post_id);
CREATE INDEX idx_geo_zip ON geographic_activity(zip_code);

-- Legislative activity table
CREATE TABLE legislative_activity (
    bill_id VARCHAR(50) PRIMARY KEY,
    session_year INTEGER NOT NULL,
    bill_number VARCHAR(50) NOT NULL,
    
    title VARCHAR(500),
    summary TEXT,
    full_text_url VARCHAR(500),
    
    -- Walkinshaw involvement
    walkinshaw_role VARCHAR(50),
    walkinshaw_position VARCHAR(20),
    vote_date TIMESTAMP,
    
    -- Bill status
    status VARCHAR(50),
    committee VARCHAR(255),
    
    -- Topics
    primary_topic VARCHAR(100),
    tags JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Legislative sentiment table
CREATE TABLE legislative_sentiment (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(50) REFERENCES legislative_activity(bill_id),
    date TIMESTAMP NOT NULL,
    
    -- Metrics
    mention_count INTEGER DEFAULT 0,
    sentiment_average FLOAT,
    awareness_score FLOAT,
    
    -- Support breakdown
    support_percentage FLOAT,
    oppose_percentage FLOAT,
    neutral_percentage FLOAT
);

CREATE INDEX idx_leg_sentiment_bill ON legislative_sentiment(bill_id);
CREATE INDEX idx_leg_sentiment_date ON legislative_sentiment(date);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Verify tables created
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```
