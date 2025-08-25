import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import re

def create_profile_visualizations(profile_data: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates visualizations for Instagram profile analysis
    Returns dictionary with different chart objects
    """
    
    if not profile_data.get("success"):
        return {"success": False, "error": "Invalid profile data"}
    
    try:
        profile = profile_data["profile"]
        posts = profile_data["recent_posts"]
        
        # Create multiple visualizations
        charts = {}
        
        # 1. Engagement Overview (Bar Chart)
        charts["engagement_overview"] = create_engagement_overview(profile, posts)
        
        # 2. Post Performance (Line Chart)
        charts["post_performance"] = create_post_performance_chart(posts)
        
        # 3. Content Type Distribution (Pie Chart)
        charts["content_distribution"] = create_content_type_chart(posts)
        
        # 4. Profile Stats (Gauge/Indicator Chart)
        charts["profile_stats"] = create_profile_stats_chart(profile)
        
        return {
            "success": True,
            "charts": charts,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "charts": {},
            "error": f"Visualization creation failed: {str(e)}"
        }

def create_engagement_overview(profile: Dict, posts: List[Dict]) -> go.Figure:
    """Creates a bar chart showing engagement metrics"""
    
    if not posts:
        # Create empty chart
        fig = go.Figure()
        fig.add_annotation(text="No posts data available", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Calculate metrics
    total_likes = sum(post.get("likes", 0) for post in posts)
    total_comments = sum(post.get("comments_count", 0) for post in posts)
    avg_likes = total_likes // len(posts) if posts else 0
    avg_comments = total_comments // len(posts) if posts else 0
    
    # Create bar chart
    metrics = ["Followers", "Following", "Total Posts", "Avg Likes/Post", "Avg Comments/Post"]
    values = [
        profile.get("followers", 0),
        profile.get("following", 0),
        profile.get("posts_count", 0),
        avg_likes,
        avg_comments
    ]
    
    fig = go.Figure(data=[
        go.Bar(x=metrics, y=values, 
               marker_color=['#E1306C', '#833AB4', '#F77737', '#FCAF45', '#405DE6'])
    ])
    
    fig.update_layout(
        title="📊 Profile Engagement Overview",
        xaxis_title="Metrics",
        yaxis_title="Count",
        template="plotly_white",
        height=400
    )
    
    return fig

def create_post_performance_chart(posts: List[Dict]) -> go.Figure:
    """Creates a line chart showing post performance over time"""
    
    if not posts:
        fig = go.Figure()
        fig.add_annotation(text="No posts data available", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Sort posts by date
    posts_sorted = sorted(posts, key=lambda x: x.get("date", ""), reverse=False)
    
    dates = []
    likes = []
    comments = []
    
    for i, post in enumerate(posts_sorted):
        try:
            date_str = post.get("date", "")
            if date_str:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                dates.append(date_obj.strftime("%m/%d"))
            else:
                dates.append(f"Post {i+1}")
        except:
            dates.append(f"Post {i+1}")
        
        likes.append(post.get("likes", 0))
        comments.append(post.get("comments_count", 0))
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add likes line
    fig.add_trace(
        go.Scatter(x=dates, y=likes, name="Likes", 
                  line=dict(color='#E1306C', width=3)),
        secondary_y=False,
    )
    
    # Add comments line
    fig.add_trace(
        go.Scatter(x=dates, y=comments, name="Comments", 
                  line=dict(color='#833AB4', width=3)),
        secondary_y=True,
    )
    
    fig.update_xaxes(title_text="Posts (Recent → Older)")
    fig.update_yaxes(title_text="Likes", secondary_y=False)
    fig.update_yaxes(title_text="Comments", secondary_y=True)
    
    fig.update_layout(
        title="📈 Post Performance Trends",
        template="plotly_white",
        height=400,
        hovermode='x'
    )
    
    return fig

def create_content_type_chart(posts: List[Dict]) -> go.Figure:
    """Creates a pie chart showing content type distribution"""
    
    if not posts:
        fig = go.Figure()
        fig.add_annotation(text="No posts data available", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    video_count = sum(1 for post in posts if post.get("is_video", False))
    photo_count = len(posts) - video_count
    
    labels = ["Photos/Carousels", "Videos/Reels"]
    values = [photo_count, video_count]
    colors = ["#F77737", "#405DE6"]
    
    fig = go.Figure(data=[
        go.Pie(labels=labels, values=values, 
               marker_colors=colors, hole=0.3)
    ])
    
    fig.update_layout(
        title="🎭 Content Type Distribution",
        template="plotly_white",
        height=400,
        showlegend=True
    )
    
    return fig

def create_profile_stats_chart(profile: Dict) -> go.Figure:
    """Creates an indicator chart showing key profile stats"""
    
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    posts_count = profile.get("posts_count", 0)
    
    # Calculate follower-to-following ratio
    ratio = followers / following if following > 0 else 0
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Followers", "Following", "Posts", "Follower Ratio"),
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]]
    )
    
    # Followers
    fig.add_trace(go.Indicator(
        mode="number",
        value=followers,
        number={"font": {"size": 40, "color": "#E1306C"}},
        title={"text": "👥"},
    ), row=1, col=1)
    
    # Following
    fig.add_trace(go.Indicator(
        mode="number", 
        value=following,
        number={"font": {"size": 40, "color": "#833AB4"}},
        title={"text": "➡️"},
    ), row=1, col=2)
    
    # Posts
    fig.add_trace(go.Indicator(
        mode="number",
        value=posts_count,
        number={"font": {"size": 40, "color": "#F77737"}},
        title={"text": "📸"},
    ), row=2, col=1)
    
    # Ratio
    fig.add_trace(go.Indicator(
        mode="number",
        value=ratio,
        number={"font": {"size": 40, "color": "#405DE6"}, "suffix": ":1"},
        title={"text": "⚖️"},
    ), row=2, col=2)
    
    fig.update_layout(
        title="📋 Profile Statistics",
        template="plotly_white",
        height=400
    )
    
    return fig

# Test function
if __name__ == "__main__":
    print("Visualization module loaded successfully!")
    print("Use this module by importing create_profile_visualizations function")
