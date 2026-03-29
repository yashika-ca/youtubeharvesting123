import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import pandas as pd
import sqlite3

import auth
from youtube_api import get_channel_data,get_videos
from analysis import show_analysis
from graph import show_graph

st.set_page_config(
    page_title="YouTube Analytics",
    layout="wide"
)

# Auto-initialize DB on startup (needed for Streamlit Cloud deployment)
def init_db():
    conn = sqlite3.connect("Youtube.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Youtube (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT,
            video_id TEXT,
            title TEXT,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            duration TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Authentication Check
if "authenticated" not in st.session_state:
    auth.show_auth_ui()
    st.stop()

with st.sidebar:
    # 1. Branding at the top
    st.image("https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=100)
    
    # 2. Account Status Info
    st.write(f"Logged in as: **{st.session_state['username']}**")
    st.divider()

    # 3. Main Navigation
    selected = option_menu(
        "Menu",
        ["Dashboard", "Channel", "Videos", "Analytics", "Graph", "Logout"],
        icons=["house", "collection", "camera-video", "bar-chart", "diagram-3", "box-arrow-right"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px"},
            "nav-link-selected": {"background-color": "#ff4b4b"},
        }
    )

    # 4. Handle Logout from menu
    if selected == "Logout":
        del st.session_state["authenticated"]
        del st.session_state["username"]
        st.rerun()


# DASHBOARD
if selected=="Dashboard":

    st.title("📊 YouTube Data Dashboard")

    # Load real data for metrics
    conn = sqlite3.connect("Youtube.db")
    db_df = pd.read_sql("SELECT * FROM Youtube", conn)
    conn.close()

    total_channels = db_df['channel'].nunique() if not db_df.empty else 0
    total_videos = len(db_df)
    total_views = db_df['views'].sum() if not db_df.empty else 0

    col1,col2,col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="card">
        <h3>Channels</h3>
        <h1>{total_channels}</h1>
        <p style="color: green;">Active</p>
        </div>
        """,unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
        <h3>Videos</h3>
        <h1>{total_videos}</h1>
        <p style="color: green;">Harvested</p>
        </div>
        """,unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
        <h3>Views</h3>
        <h1>{total_views // 1000000}M</h1>
        <p style="color: green;">Combined</p>
        </div>
        """,unsafe_allow_html=True)

    st.divider()

    if not db_df.empty:
        # Real Views Distribution
        st.subheader("Views Distribution by Channel")
        channel_data = db_df.groupby("channel")["views"].sum().reset_index()
        fig = px.pie(channel_data, names="channel", values="views", title="Real-time Views Mix", hole=0.3)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available yet. Start by fetching channel data!")


# End of Dashboard section

# Channel Profile Cards
elif selected=="Channel":

    st.title("📺 Channel Profile")

    channel = st.text_input("Enter Channel Name")

    if st.button("Fetch Channel"):

        data = get_channel_data(channel)
        if data:
            col1,col2 = st.columns([1,3])

            with col1:
                if "logo" in data:
                    st.image(data["logo"], width=150)
                else:
                    st.image("https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=150)

            with col2:

                st.subheader(data["channel_name"])

                st.metric("Subscribers",data["subscribers"])
                st.metric("Views",data["views"])
        else:
            st.error("Channel not found.")

# Videos with YouTube Thumbnails
elif selected=="Videos":

    st.title("🎬 Channel Videos")

    channel = st.text_input("Channel Name")

    if st.button("Fetch Videos"):

        df = get_videos(channel)
        
        if df is not None and not df.empty:
            for i,row in df.iterrows():

                col1,col2 = st.columns([1,3])

                with col1:

                    thumbnail = f"https://img.youtube.com/vi/{row['video_id']}/0.jpg"

                    st.image(thumbnail)

                with col2:

                    st.subheader(row["title"])
                    st.write(f"👁 Views : {row['views']}")
                    st.write(f"👍 Likes : {row['likes']}")
        else:
            st.warning("No videos found.")

elif selected=="Analytics":
    show_analysis()

elif selected=="Graph":
    st.title("🔗 Channel Video Graph")
    
    # Load available channels from DB
    try:
        conn = sqlite3.connect("Youtube.db")
        db_df = pd.read_sql("SELECT DISTINCT channel FROM Youtube", conn)
        conn.close()
        available_channels = db_df['channel'].tolist()
    except Exception:
        available_channels = []

    if available_channels:
        channel = st.selectbox("Select a Harvested Channel", available_channels)
        if st.button("Generate Graph"):
            show_graph(channel)
    else:
        st.warning("No data found in the database. Please go to the 'Videos' tab and fetch some channel data first!")


# The post-login sidebar handle Logout now.
