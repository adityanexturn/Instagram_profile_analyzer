import google.generativeai as genai
from typing import Dict, Any, List, Optional
import json

def configure_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

def _aggregate_post_stats(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not posts:
        return {"avg_likes": 0, "avg_comments": 0, "video_ratio": 0.0}
    total_likes = sum(p.get("likes", 0) for p in posts)
    total_comments = sum(p.get("comments_count", 0) for p in posts)
    video_count = sum(1 for p in posts if p.get("is_video"))
    n = len(posts)
    return {
        "avg_likes": total_likes // n,
        "avg_comments": total_comments // n,
        "video_ratio": (video_count / n) if n else 0.0,
    }

def create_structured_prompt(profile: Dict[str, Any], posts: List[Dict[str, Any]]) -> str:
    stats = _aggregate_post_stats(posts)
    # Build post samples as lightweight XML-like tags
    post_samples = "".join(
        f"<post><caption_preview>{(p.get('caption') or '').replace('<',' ').replace('>',' ')}</caption_preview></post>"
        for p in posts
    )
    prompt = f"""
You are an expert social media analyst. Your task is to analyze the provided Instagram profile data and generate a structured JSON output. Do not include any introductory text, markdown formatting, or explanations. Return only a valid JSON object.

<profile_data>
Username: {profile.get('username')}
Followers: {profile.get('followers')}
Following: {profile.get('following')}
Posts Count: {profile.get('posts_count')}
Bio: {profile.get('biography')}
External URL: {profile.get('external_url')}
Is Verified: {profile.get('is_verified')}
</profile_data>

<recent_posts_summary>
Total posts analyzed: {len(posts)}
Average Likes: {stats['avg_likes']}
Average Comments: {stats['avg_comments']}
Video Ratio: {stats['video_ratio']:.2f}
</recent_posts_summary>

<post_samples>
{post_samples}
</post_samples>

Based on the provided data, return a single JSON object with this schema:
{{
  "summary": "A concise 4-5 sentence overview of the profile's purpose, content style, and audience.",
  "insights": {{
    "content_strategy": "Analyze primary content themes, formats (photo/video), and overall strategy. Estimate posting frequency if possible.",
    "audience_engagement": "Evaluate audience interaction based on likes, comments, and the nature of captions.",
    "brand_analysis": "Assess brand identity clarity (personal, business, influencer) and niche.",
    "growth_indicators": "Identify potential growth drivers or blockers (CTAs, follower/following ratio, content quality).",
    "content_performance": "Comment on recent post performance patterns and standout content types."
  }}
}}
Ensure the output is strictly valid JSON with double quotes and no trailing commas.
"""
    return prompt

def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        newline_index = t.find("\n")
        if newline_index != -1:
            # Strip the opening fence and any optional language identifier line
            t = t[newline_index + 1:]
        else:
            # Just fences without content
            t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()

def _validate_and_normalize(parsed: Any) -> Dict[str, Any]:
    """
    Ensure required keys exist and types are strings; provide safe fallbacks.
    """
    result = {"summary": "", "insights": {}}
    if isinstance(parsed, dict):
        summary = parsed.get("summary", "")
        insights = parsed.get("insights", {})
        if not isinstance(summary, str):
            summary = str(summary)
        if not isinstance(insights, dict):
            insights = {}
        # Normalize insight fields
        def s(v): return v if isinstance(v, str) else str(v)
        insights_out = {
            "content_strategy": s(insights.get("content_strategy", "")),
            "audience_engagement": s(insights.get("audience_engagement", "")),
            "brand_analysis": s(insights.get("brand_analysis", "")),
            "growth_indicators": s(insights.get("growth_indicators", "")),
            "content_performance": s(insights.get("content_performance", "")),
        }
        result["summary"] = summary
        result["insights"] = insights_out
    else:
        # Fallback minimal structure
        result = {
            "summary": "Analysis completed but response format was unexpected.",
            "insights": {
                "content_strategy": "",
                "audience_engagement": "",
                "brand_analysis": "",
                "growth_indicators": "",
                "content_performance": "",
            },
        }
    return result

def analyze_instagram_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze Instagram profile data using Gemini with deterministic prompt and safe parsing.
    """
    if not profile_data.get("success"):
        return {
            "success": False,
            "error": "Invalid profile data provided",
            "summary": "",
            "insights": {},
        }
    try:
        profile = profile_data["profile"]
        posts = profile_data["recent_posts"]
        prompt = create_structured_prompt(profile, posts)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = getattr(response, "text", "") or ""
        cleaned = _strip_markdown_fences(text)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # light retry: try to find first/last brace to salvage JSON
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(cleaned[start:end+1])
                except Exception:
                    parsed = {}
            else:
                parsed = {}
        normalized = _validate_and_normalize(parsed)
        return {
            "success": True,
            "error": None,
            "summary": normalized["summary"],
            "insights": normalized["insights"],
            "raw_response": text,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI analysis failed: {str(e)}",
            "summary": "",
            "insights": {},
        }

# Test hook
if __name__ == "__main__":
    print("AI agent module ready with structured prompting and safe parsing.")
