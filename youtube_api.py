import os
import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from datetime import timedelta
import sqlite3
from dotenv import load_dotenv

load_dotenv()

_youtube_client = None

def get_youtube_client():
    global _youtube_client
    if _youtube_client is not None:
        return _youtube_client
    try:
        api_key = st.secrets["YOUTUBE_API_KEY"]
    except Exception:
        api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        return None
    try:
        _youtube_client = build('youtube', 'v3', developerKey=api_key)
        return _youtube_client
    except Exception:
        return None


# Category mapping from YouTube topic categories URLs
TOPIC_MAP = {
    "Beauty": ["Beauty", "Cosmetics", "Makeup", "Fashion"],
    "Gaming": ["Gaming", "Video game culture", "Action-adventure game", "Role-playing video game"],
    "Tech": ["Technology", "Gadgets", "Science", "Computers"],
    "Entertainment": ["Entertainment", "Movies", "TV shows", "Music"],
    "Food": ["Food", "Cooking", "Cuisine", "Lifestyle"],
    "Education": ["Knowledge", "Education", "Learning", "Science"],
    "Sports": ["Sports", "Athletics", "Football", "Basketball"]
}

# Industry benchmarks for audience demographics based on category
AUDIENCE_BENCHMARKS = {
    "Beauty": {"male": 18, "female": 78, "under_18": 16, "description": "typical for beauty content. Lean into tutorials, deep-dives and challenge formats."},
    "Gaming": {"male": 68, "female": 28, "under_18": 45, "description": "heavily geared towards young gamers. Focus on high-energy hooks and trending game mechanics."},
    "Tech": {"male": 82, "female": 15, "under_18": 22, "description": "concentrated in tech-savvy male viewers. Emphasize specs, detail-oriented comparisons, and long-term utility."},
    "Food": {"male": 42, "female": 54, "under_18": 18, "description": "broad appeal across genders. Storytelling and high-quality aesthetic shots are key to retention."},
    "Default": {"male": 45, "female": 45, "under_18": 25, "description": "balanced audience. Test various formats to find your channel's unique sweet spot."}
}

def get_channel_id(channel_name):
    try:
        yt = get_youtube_client()
        if not yt: return None
        search = yt.search().list(part="id", q=channel_name, type="channel", maxResults=1).execute()
        if not search.get("items"): return None
        return search["items"][0]["id"]["channelId"]
    except Exception: return None

def get_channel_data(channel_name):
    yt = get_youtube_client()
    if not yt:
        return None
    try:
        channel_id = get_channel_id(channel_name)
        if not channel_id: return None
        
        channel_resp = yt.channels().list(part="snippet,statistics,topicDetails", id=channel_id).execute()["items"][0]
        snippet = channel_resp["snippet"]
        stats = channel_resp["statistics"]
        topics = channel_resp.get("topicDetails", {}).get("topicCategories", [])
        
        # Determine category
        category = "General"
        for topic_url in topics:
            for cat_name, keywords in TOPIC_MAP.items():
                if any(kw.lower() in topic_url.lower() for kw in keywords):
                    category = cat_name
                    break
            if category != "General": break
            
        data = {
            "channel_id": channel_id,
            "channel_name": snippet["title"],
            "description": snippet.get("description", ""),
            "subscribers": stats.get("subscriberCount", "0"),
            "views": stats.get("viewCount", "0"),
            "video_count": stats.get("videoCount", "0"),
            "logo": snippet["thumbnails"]["high"]["url"],
            "published_at": snippet.get("publishedAt", ""),
            "country": snippet.get("country", "Global"),
            "category": category
        }
        return data
    except Exception as e:
        print(f"Error in get_channel_data: {e}")
        return None

def parse_duration(duration):
    if not duration:
        return "0:00:00"
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return "0:00:00"
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return str(timedelta(hours=h, minutes=m, seconds=s))

def get_videos(channel_name):
    yt = get_youtube_client()
    if not yt:
        return None
    try:
        search = yt.search().list(part="id", q=channel_name, type="channel", maxResults=1).execute()
        if not search.get("items"):
            return None
            
        channel_id = search["items"][0]["id"]["channelId"]
        channel = yt.channels().list(part="snippet,contentDetails", id=channel_id).execute()["items"][0]
        playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        
        videos = []
        playlist_items = yt.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=5).execute()
        
        for item in playlist_items["items"]:
            vid = item["snippet"]["resourceId"]["videoId"]
            try:
                v = yt.videos().list(part="snippet,statistics,contentDetails", id=vid).execute()["items"][0]
                videos.append({
                    "channel": channel["snippet"]["title"],
                    "video_id": vid,
                    "title": v["snippet"]["title"],
                    "views": int(v["statistics"].get("viewCount", 0)),
                    "likes": int(v["statistics"].get("likeCount", 0)),
                    "comments": int(v["statistics"].get("commentCount", 0)),
                    "duration": parse_duration(v["contentDetails"]["duration"])
                })
            except Exception:
                continue
                
        df = pd.DataFrame(videos)
        
        # Save to database logic based on original file
        if not df.empty:
            conn = sqlite3.connect("Youtube.db")
            df.to_sql("Youtube", conn, if_exists="append", index=False)
            conn.commit()
            conn.close()
            
        return df
    except Exception as e:
        print(f"Error in get_videos: {e}")
        return None
