import streamlit as st
from streamlit_option_menu import option_menu
from youtube_api import get_channel_data, get_videos
from analysis import show_analysis
from graph import show_graph

def dashboard():
    with st.sidebar:
        selected = option_menu(
            "Menu",
            ["Home","Channel Data","Videos","Analytics","Graph","Logout"],
            icons=["house","collection","camera-video","bar-chart","diagram-3","box-arrow-right"]
        )

    if selected == "Home":
        st.title("📊 YouTube Data Harvesting Dashboard")
        col1,col2,col3 = st.columns(3)
        col1.metric("Channels","10")
        col2.metric("Videos","500")
        col3.metric("Views","2M")

    elif selected == "Channel Data":
        channel = st.text_input("Enter Channel Name")
        if st.button("Fetch Channel"):
            data = get_channel_data(channel)
            if data:
                st.success("Channel Data Retrieved")
                st.json(data)
            else:
                st.error("Channel not found")

    elif selected == "Videos":
        channel = st.text_input("Enter Channel Name")
        if st.button("Fetch Videos"):
            df = get_videos(channel)
            if df is not None and not df.empty:
                st.dataframe(df)
            else:
                st.error("No videos found or error occurred")

    elif selected == "Analytics":
        show_analysis()

    elif selected == "Graph":
        show_graph()

    elif selected == "Logout":
        del st.session_state["user"]
        st.rerun()
