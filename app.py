import streamlit as st
import sys
import os
import time
import base64
import pandas as pd
import plotly.graph_objects as go

# Ensure we can import local src modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from data_handler import get_instagram_profile_data
from ai_agents import configure_gemini, analyze_instagram_profile
from visualization import create_profile_visualizations

# Page configuration
st.set_page_config(
    page_title="Instagram Profile Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Function to encode image to base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Custom CSS for stunning Instagram-themed UI
st.markdown("""
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@900&display=swap');

/* Main App Styling */
.stApp {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: #ffffff;
}

/* Header Container */
.header-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    margin: 2rem 0;
    padding: 1rem;
}

/* Animated Instagram Logo (Unchanged) */
.instagram-logo {
    width: 100px;
    height: 100px;
    margin-right: 30px;
    animation: pulse 2s ease-in-out infinite;
    filter: drop-shadow(0 0 20px rgba(253, 29, 29, 0.5));
    border-radius: 20px;
}

@keyframes pulse {
    0%, 100% { 
        transform: scale(1);
        filter: drop-shadow(0 0 20px rgba(253, 29, 29, 0.5));
    }
    50% { 
        transform: scale(1.05);
        filter: drop-shadow(0 0 30px rgba(253, 29, 29, 0.8));
    }
}

/* Simplified Instagram Title */
.animated-title {
    font-family: 'Poppins', sans-serif;
    font-size: 3.8rem;
    font-weight: 900;
    color: #E1306C; /* Simple, solid Instagram pink color */
    white-space: nowrap;
    letter-spacing: 2px;
    margin: 0;
}

/* Custom Button Styling */
.stButton > button {
    margin-top: 28px; /* <-- ADD THIS LINE to align the button */
    background: linear-gradient(45deg, #833AB4, #FD1D1D, #FCB045);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 0.5rem 2rem;
    font-weight: bold;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(131, 58, 180, 0.4);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(131, 58, 180, 0.6);
}

.stButton > button:disabled {
    background: #666666;
    color: #cccccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

/* Enhanced Metrics */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(131, 58, 180, 0.1), rgba(253, 29, 29, 0.1));
    border: 1px solid rgba(131, 58, 180, 0.3);
    padding: 1rem;
    border-radius: 15px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* Enhanced Info Boxes */
.stAlert {
    background: linear-gradient(135deg, rgba(131, 58, 180, 0.15), rgba(253, 29, 29, 0.15));
    border-left: 4px solid #FD1D1D;
    border-radius: 10px;
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(131, 58, 180, 0.2), rgba(253, 29, 29, 0.2));
    border-radius: 10px;
    font-weight: bold;
}

/* Text Input Styling */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 2px solid rgba(131, 58, 180, 0.5);
    border-radius: 15px;
    padding: 0.75rem 1rem;
}

.stTextInput > div > div > input:focus {
    border-color: #FD1D1D;
    box-shadow: 0 0 10px rgba(253, 29, 29, 0.5);
}

/* Hide Streamlit Menu and Footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #2d2d2d;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, #833AB4, #FD1D1D);
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# Try to load and display the Instagram logo
try:
    # Get the base64 string of the image
    img_base64 = get_base64_of_bin_file("instagram.png")
    
    # Header with Instagram Logo and Title (centered)
    st.markdown(f"""
    <div class="header-container">
        <img src="data:image/png;base64,{img_base64}" class="instagram-logo" alt="Instagram Logo">
        <h1 class="animated-title">Instagram Profile Analyzer</h1>
    </div>
    """, unsafe_allow_html=True)
    
except FileNotFoundError:
    # Fallback if instagram.png is not found
    st.markdown("""
    <div class="header-container">
        <div style="width: 100px; height: 100px; margin-right: 30px; background: linear-gradient(45deg, #833AB4, #FD1D1D, #FCB045); border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 40px; animation: pulse 2s ease-in-out infinite;">📷</div>
        <h1 class="animated-title">Instagram Profile Analyzer</h1>
    </div>
    """, unsafe_allow_html=True)

# Session state initialization
if "profile_data" not in st.session_state:
    st.session_state.profile_data = None
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False

# Configure Gemini AI
try:
    configure_gemini(st.secrets["GEMINI_API_KEY"])
    st.success("🤖 AI Engine Connected Successfully!")
except Exception as e:
    st.error(f"❌ Failed to configure AI: {e}")
    st.stop()

# Input section with enhanced styling
st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    username = st.text_input(
        "🔍 Enter Instagram Username", 
        placeholder="e.g., google, nasa, nike",
        help="Enter the username without @ symbol",
        disabled=st.session_state.is_analyzing
    )

with col2:
    analyze_btn = st.button(
        "🚀 Analyze Profile", 
        type="primary", 
        use_container_width=True,
        disabled=st.session_state.is_analyzing or not username
    )

# Enhanced Analysis Process with Status Updates
if analyze_btn and username:
    if username.strip():
        st.session_state.is_analyzing = True
        
        with st.status("🔍 Starting analysis...", expanded=True) as status:
            # Step 1: Data Scraping
            status.write("🔍 Scraping profile data...")
            profile_data = get_instagram_profile_data(username.strip())
            
            if not profile_data.get("success"):
                status.update(label="Analysis Failed!", state="error")
                st.error(f"❌ Failed to fetch profile: {profile_data.get('error', 'Unknown error')}")
                st.session_state.is_analyzing = False
                st.stop()
            
            if profile_data.get("profile", {}).get("is_private"):
                status.update(label="Analysis Failed!", state="error")
                st.error("🔒 This profile is private. Please provide a public profile.")
                st.session_state.is_analyzing = False
                st.stop()
            
            st.session_state.profile_data = profile_data
            status.write("✅ Profile data collected successfully!")
            
            # Step 2: AI Analysis
            status.write("🧠 Generating AI insights...")
            ai_analysis = analyze_instagram_profile(profile_data)
            
            if not ai_analysis.get("success"):
                status.update(label="Analysis Failed!", state="error")
                st.error(f"❌ AI analysis failed: {ai_analysis.get('error', 'Unknown error')}")
                st.session_state.is_analyzing = False
                st.stop()
            
            st.session_state.ai_analysis = ai_analysis
            status.write("✅ AI analysis completed!")
            
            # Step 3: Visualization
            status.write("📊 Creating visualizations...")
            time.sleep(0.5)  # Brief pause for effect
            status.write("✅ All done!")
            
            status.update(label="🎉 Analysis Complete!", state="complete", expanded=False)
        
        st.session_state.is_analyzing = False

# Display Results
if st.session_state.profile_data and st.session_state.ai_analysis:
    profile_data = st.session_state.profile_data
    ai_analysis = st.session_state.ai_analysis
    profile = profile_data.get("profile", {})
    
    st.markdown("---")
    
    # Profile Header
    st.markdown(f"## 👤 @{profile.get('username')} • {profile.get('full_name') or ''}")
    if profile.get('biography'):
        st.markdown(f"*{profile.get('biography')}*")
    
    # Main Metrics (Top Row)
    m_col1, m_col2, m_col3 = st.columns(3)
    
    with m_col1:
        st.metric(
            "👥 Followers", 
            f"{profile.get('followers', 0):,}",
            help="Total number of followers"
        )
    
    with m_col2:
        st.metric(
            "📝 Posts", 
            f"{profile.get('posts_count', 0):,}",
            help="Total posts published"
        )
    
    with m_col3:
        st.metric(
            "➡️ Following", 
            f"{profile.get('following', 0):,}",
            help="Number of accounts followed"
        )
    
    # AI Summary in styled container
    st.markdown("### 🧠 AI-Generated Summary")
    summary = ai_analysis.get("summary", "No summary available")
    st.info(summary)
    
    # Collapsible Detailed Insights
    st.markdown("### 🔍 Detailed Analysis")
    
    insights = ai_analysis.get("insights", {})
    
    with st.expander("🎯 Content Strategy", expanded=False):
        st.write(insights.get("content_strategy", "No analysis available"))
    
    with st.expander("💬 Audience Engagement", expanded=False):
        st.write(insights.get("audience_engagement", "No analysis available"))
    
    with st.expander("🎭 Brand Analysis", expanded=False):
        st.write(insights.get("brand_analysis", "No analysis available"))
    
    with st.expander("📈 Growth Indicators", expanded=False):
        st.write(insights.get("growth_indicators", "No analysis available"))
    
    with st.expander("⚡ Content Performance", expanded=False):
        st.write(insights.get("content_performance", "No analysis available"))
    
    # Enhanced Engagement Chart
    st.markdown("### 📊 Engagement Analysis")
    
    if profile_data.get("recent_posts"):
        posts = profile_data["recent_posts"]
        total_likes = sum(post.get("likes", 0) for post in posts)
        total_comments = sum(post.get("comments_count", 0) for post in posts)
        avg_likes = total_likes // len(posts) if posts else 0
        avg_comments = total_comments // len(posts) if posts else 0
        
        # Create simplified engagement chart
        fig = go.Figure(data=[
            go.Bar(
                x=['Average Likes per Post', 'Average Comments per Post'],
                y=[avg_likes, avg_comments],
                marker_color=['#E1306C', '#833AB4'],
                text=[f'{avg_likes:,}', f'{avg_comments:,}'],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="📊 Average Engagement per Post",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Other Visualizations
    viz_data = create_profile_visualizations(profile_data, ai_analysis)
    
    if viz_data.get("success"):
        charts = viz_data.get("charts", {})
        
        v_col1, v_col2 = st.columns(2)
        
        with v_col1:
            if "post_performance" in charts:
                st.plotly_chart(charts["post_performance"], use_container_width=True)
            
            if "content_distribution" in charts:
                st.plotly_chart(charts["content_distribution"], use_container_width=True)
        
        with v_col2:
            if "profile_stats" in charts:
                st.plotly_chart(charts["profile_stats"], use_container_width=True)
    
    # Enhanced Posts Table
    if profile_data.get("recent_posts"):
        st.markdown("### 📱 Recent Posts Analysis")
        
        posts_data = []
        for post in profile_data["recent_posts"]:
            posts_data.append({
                "Date": (post.get("date") or "")[:10],
                "Likes": f"{post.get('likes', 0):,}",
                "Comments": f"{post.get('comments_count', 0):,}",
                "Type": "🎥 Video" if post.get("is_video") else "📸 Photo",
                "Caption Preview": (post.get("caption") or "No caption")[:100] + ("..." if len(post.get("caption", "")) > 100 else "")
            })
        
        df = pd.DataFrame(posts_data)
        
        st.dataframe(df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; padding: 2rem;'>
        <p><small>🔒 This tool analyzes public Instagram profiles only • No data is stored</small></p>
    </div>
    """, 
    unsafe_allow_html=True
)