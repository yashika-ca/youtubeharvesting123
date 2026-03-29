import streamlit as st
import pandas as pd
import sqlite3
import re
from googleapiclient.discovery import build
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

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
def run():
    st.title("YouTube Data Harvesting")

    channel_name = st.text_input("Enter Channel Name")

    if st.button("Fetch Data"):
        if not channel_name:
            st.warning("Please enter a channel name")
            return

        try:
            youtube = build("youtube", "v3", developerKey=API_KEY)

            # -------- CHANNEL SEARCH (SAFE) --------
            try:
                search = youtube.search().list(
                    part="id",
                    q=channel_name,
                    type="channel",
                    maxResults=1
                ).execute()
            except Exception:
                st.error("❌ YouTube API quota exceeded. Please try again after 24 hours.")
                return

            if not search.get("items"):
                st.warning("Channel not found")
                return

            channel_id = search["items"][0]["id"]["channelId"]

            # -------- CHANNEL DETAILS --------
            channel = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            ).execute()["items"][0]

            playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

            videos = []
            next_page = None

            # -------- VIDEO LOOP (LIMITED & SAFE) --------
            while True:
                playlist_items = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=5,   # LIMIT TO SAVE QUOTA
                    pageToken=next_page
                ).execute()

                for item in playlist_items["items"]:
                    vid = item["snippet"]["resourceId"]["videoId"]

                    try:
                        v = youtube.videos().list(
                            part="snippet,statistics,contentDetails",
                            id=vid
                        ).execute()["items"][0]
                    except Exception:
                        continue   # skip if quota issue mid-loop

                    videos.append({
                        "channel": channel["snippet"]["title"],
                        "title": v["snippet"]["title"],
                        "views": int(v["statistics"].get("viewCount", 0)),
                        "likes": int(v["statistics"].get("likeCount", 0)),
                        "comments": int(v["statistics"].get("commentCount", 0)),
                        "duration": parse_duration(v["contentDetails"]["duration"])
                    })

                break  # 🔴 STOP AFTER FIRST PAGE (VERY IMPORTANT)

            if not videos:
                st.warning("No videos fetched due to API limits")
                return

            df = pd.DataFrame(videos)
            st.dataframe(df)

            conn = sqlite3.connect("Youtube.db")
            df.to_sql("Youtube", conn, if_exists="append", index=False)
            conn.commit()
            conn.close()

            st.success(f"{len(df)} videos saved successfully")

        except Exception as e:
            st.error("Unexpected error occurred. Please try later.")
