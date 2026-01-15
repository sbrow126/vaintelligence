"""
VA-11 Constituent Intelligence Dashboard
Streamlit-based interface for James Walkinshaw
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database.models import (
    SocialMediaPost, SentimentAnalysis, Topic, PostTopic,
    TrendTracking, Influencer, get_connection_string
)
import os

# Page config
st.set_page_config(
    page_title="VA-11 Constituent Intelligence",
    page_icon="🏛️",
    layout="wide"
)

# Initialize database connection
@st.cache_resource
def init_connection():
    engine = create_engine(get_connection_string())
    Session = sessionmaker(bind=engine)
    return Session()

db = init_connection()

# Sidebar
st.sidebar.title("VA-11 Intelligence Platform")
st.sidebar.markdown("### Representative James Walkinshaw")
st.sidebar.markdown("---")

# Date range selector
date_range = st.sidebar.selectbox(
    "Time Period",
    ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
    index=1
)

# Calculate date filter
if date_range == "Last 24 Hours":
    start_date = datetime.utcnow() - timedelta(days=1)
elif date_range == "Last 7 Days":
    start_date = datetime.utcnow() - timedelta(days=7)
elif date_range == "Last 30 Days":
    start_date = datetime.utcnow() - timedelta(days=30)
else:
    start_date = datetime.utcnow() - timedelta(days=90)

# Platform filter
platforms = st.sidebar.multiselect(
    "Platforms",
    ["reddit", "bluesky"],
    default=["reddit", "bluesky"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Last Updated:** " + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

# Main dashboard
st.title("🏛️ VA-11 Constituent Intelligence Dashboard")
st.markdown("### Real-Time Social Media Sentiment Analysis")

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

# Total mentions
total_posts = db.query(func.count(SocialMediaPost.post_id)).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).scalar()

# Average sentiment
avg_sentiment = db.query(func.avg(SentimentAnalysis.sentiment_score)).join(
    SocialMediaPost
).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).scalar() or 0

# Total engagement
total_engagement = db.query(func.sum(SocialMediaPost.engagement_score)).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).scalar() or 0

# Unique voices
unique_authors = db.query(func.count(func.distinct(SocialMediaPost.author_id))).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).scalar()

with col1:
    st.metric("Total Mentions", f"{total_posts:,}")

with col2:
    sentiment_emoji = "😊" if avg_sentiment > 0.2 else "😐" if avg_sentiment > -0.2 else "😞"
    st.metric("Avg Sentiment", f"{avg_sentiment:.2f} {sentiment_emoji}")

with col3:
    st.metric("Total Engagement", f"{int(total_engagement):,}")

with col4:
    st.metric("Unique Voices", f"{unique_authors:,}")

st.markdown("---")

# Top Issues Section
st.header("📊 Top Issues This Period")

# Query top topics
top_topics_query = db.query(
    Topic.name,
    Topic.category,
    func.count(PostTopic.post_id).label('mention_count'),
    func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment')
).join(PostTopic).join(SocialMediaPost).join(SentimentAnalysis).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).group_by(Topic.topic_id, Topic.name, Topic.category).order_by(
    func.count(PostTopic.post_id).desc()
).limit(10).all()

if top_topics_query:
    topics_df = pd.DataFrame(top_topics_query, columns=['Topic', 'Category', 'Mentions', 'Sentiment'])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Bar chart of mentions
        fig = px.bar(
            topics_df,
            x='Mentions',
            y='Topic',
            orientation='h',
            title='Mention Volume by Issue',
            color='Sentiment',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Issue Breakdown")
        for _, row in topics_df.iterrows():
            sentiment_color = "🟢" if row['Sentiment'] > 0.2 else "🔴" if row['Sentiment'] < -0.2 else "🟡"
            st.markdown(f"**{row['Topic']}** {sentiment_color}")
            st.markdown(f"└ {row['Mentions']} mentions | Sentiment: {row['Sentiment']:.2f}")
            st.markdown("")

else:
    st.info("No topic data available for this period.")

st.markdown("---")

# Sentiment Over Time
st.header("📈 Sentiment Trends")

# Query daily sentiment
daily_sentiment = db.query(
    func.date(SocialMediaPost.timestamp).label('date'),
    func.count(SocialMediaPost.post_id).label('mentions'),
    func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment')
).join(SentimentAnalysis).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).group_by(func.date(SocialMediaPost.timestamp)).order_by(
    func.date(SocialMediaPost.timestamp)
).all()

if daily_sentiment:
    daily_df = pd.DataFrame(daily_sentiment, columns=['Date', 'Mentions', 'Sentiment'])
    
    fig = go.Figure()
    
    # Add sentiment line
    fig.add_trace(go.Scatter(
        x=daily_df['Date'],
        y=daily_df['Sentiment'],
        name='Average Sentiment',
        line=dict(color='#1f77b4', width=3),
        yaxis='y'
    ))
    
    # Add mention volume bars
    fig.add_trace(go.Bar(
        x=daily_df['Date'],
        y=daily_df['Mentions'],
        name='Mention Volume',
        marker=dict(color='lightblue', opacity=0.3),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Sentiment and Volume Over Time',
        yaxis=dict(title='Sentiment Score', range=[-1, 1]),
        yaxis2=dict(title='Mentions', overlaying='y', side='right'),
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No sentiment trend data available.")

st.markdown("---")

# Recent High-Engagement Posts
st.header("🔥 High-Engagement Posts")

high_engagement = db.query(SocialMediaPost, SentimentAnalysis).join(
    SentimentAnalysis
).filter(
    SocialMediaPost.timestamp >= start_date,
    SocialMediaPost.platform.in_(platforms)
).order_by(SocialMediaPost.engagement_score.desc()).limit(10).all()

if high_engagement:
    for post, sentiment in high_engagement:
        with st.expander(f"**{post.platform.upper()}** | {post.timestamp.strftime('%Y-%m-%d %H:%M')} | Engagement: {post.engagement_score}"):
            st.markdown(f"**Author:** {post.author_username}")
            st.markdown(f"**Sentiment:** {sentiment.sentiment_category.upper()} ({sentiment.sentiment_score:.2f})")
            st.markdown(f"**Content:**")
            st.markdown(f"> {post.content[:500]}{'...' if len(post.content) > 500 else ''}")
            st.markdown(f"[View Original]({post.url})")
else:
    st.info("No high-engagement posts found.")

st.markdown("---")

# Platform Breakdown
st.header("📱 Platform Distribution")

col1, col2 = st.columns(2)

with col1:
    # Posts by platform
    platform_counts = db.query(
        SocialMediaPost.platform,
        func.count(SocialMediaPost.post_id).label('count')
    ).filter(
        SocialMediaPost.timestamp >= start_date,
        SocialMediaPost.platform.in_(platforms)
    ).group_by(SocialMediaPost.platform).all()
    
    if platform_counts:
        platform_df = pd.DataFrame(platform_counts, columns=['Platform', 'Count'])
        fig = px.pie(platform_df, values='Count', names='Platform', title='Posts by Platform')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # Sentiment by platform
    platform_sentiment = db.query(
        SocialMediaPost.platform,
        func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment')
    ).join(SentimentAnalysis).filter(
        SocialMediaPost.timestamp >= start_date,
        SocialMediaPost.platform.in_(platforms)
    ).group_by(SocialMediaPost.platform).all()
    
    if platform_sentiment:
        sent_df = pd.DataFrame(platform_sentiment, columns=['Platform', 'Sentiment'])
        fig = px.bar(sent_df, x='Platform', y='Sentiment', title='Average Sentiment by Platform', 
                     color='Sentiment', color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Built by Dr. Shallon Brown | CTO Advisor Pro | Powered by GCP")
