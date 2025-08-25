import streamlit as st
import instaloader
from datetime import datetime
from typing import Dict, Any, List
import time

def _preprocess_posts(posts: List[Dict[str, Any]], max_posts: int = 8, caption_limit: int = 200) -> List[Dict[str, Any]]:
    """Limit post count and truncate captions to reduce LLM token usage."""
    processed = []
    for post in posts[:max_posts]:
        caption = post.get("caption") or ""
        if len(caption) > caption_limit:
            caption = caption[:caption_limit] + "..."
        processed.append({
            "date": post.get("date"),
            "likes": post.get("likes", 0),
            "comments_count": post.get("comments_count", 0),
            "caption": caption,
            "is_video": post.get("is_video", False),
        })
    return processed

@st.cache_data(ttl=3600)
def get_instagram_profile_data(username: str) -> Dict[str, Any]:
    """
    Scrapes Instagram profile data using instaloader with error handling and Streamlit's cache.
    Returns a dictionary with profile information and recent posts (preprocessed).
    """
    try:
        loader = instaloader.Instaloader()
        loader.context.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        loader.context.sleep = True

        profile = instaloader.Profile.from_username(loader.context, username)

        if profile.is_private:
            return {
                "profile": {"username": username, "is_private": True},
                "recent_posts": [],
                "scrape_timestamp": datetime.now().isoformat(),
                "success": False,
                "error": "Profile is private. Please provide a public profile.",
            }

        profile_data = {
            "username": profile.username,
            "full_name": profile.full_name,
            "biography": profile.biography,
            "followers": profile.followers,
            "following": profile.followees,
            "posts_count": profile.mediacount,
            "is_verified": profile.is_verified,
            "is_private": profile.is_private,
            "external_url": profile.external_url,
        }

        # Collect posts safely
        raw_posts = []
        count = 0
        max_collect = 12
        try:
            for post in profile.get_posts():
                if count >= max_collect:
                    break
                raw_posts.append({
                    "date": post.date.isoformat(),
                    "likes": post.likes,
                    "comments_count": post.comments,
                    "caption": post.caption or "",
                    "is_video": post.is_video,
                })
                count += 1
                time.sleep(0.5)
        except Exception:
            # Continue with what we have, even if post scraping is interrupted
            pass

        # Preprocess for LLM cost/latency
        recent_posts = _preprocess_posts(raw_posts, max_posts=8, caption_limit=200)

        result = {
            "profile": profile_data,
            "recent_posts": recent_posts,
            "scrape_timestamp": datetime.now().isoformat(),
            "success": True,
            "error": None,
        }
        return result

    except Exception as e:
        msg = str(e)
        if "data" in msg:
            msg = "Instagram changed their response format. Try again later or try a different profile."
        elif "404" in msg:
            msg = f"Profile '{username}' not found."
        elif "429" in msg:
            msg = "Rate limited by Instagram. Please wait a few minutes and try again."
        return {
            "profile": {},
            "recent_posts": [],
            "scrape_timestamp": datetime.now().isoformat(),
            "success": False,
            "error": msg,
        }