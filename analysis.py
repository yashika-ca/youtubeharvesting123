import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from youtube_api import get_channel_data, AUDIENCE_BENCHMARKS, get_videos
import datetime

def format_number(num):
    num = float(num)
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(int(num))

def show_analysis():
    st.title("📈 Channel Analytics")
    st.write("Search any YouTube channel to get real stats + audience insights")

    search_query = st.text_input("Enter YouTube Channel Name", placeholder="e.g. Irfan views")
    
    # Layout for Generate Button and Auto-Harvest Toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        generate_clicked = st.button("🚀 Generate Data", use_container_width=True)
    with col2:
        auto_harvest = st.toggle("🤖 Auto-Harvest", value=False)

    if search_query:
        if generate_clicked or auto_harvest:
            with st.spinner(f"Harvesting videos for {search_query}..."):
                harvested_df = get_videos(search_query)
                if harvested_df is not None and not harvested_df.empty:
                    st.success(f"Successfully harvested {len(harvested_df)} videos!")
                else:
                    st.warning("No new videos to harvest or API quota reached.")
        
        st.divider()

        data = get_channel_data(search_query)
        if data:
            # Profile Card
            col_img, col_info = st.columns([1, 4])
            with col_img:
                st.image(data["logo"], width=150)
            
            with col_info:
                st.markdown(f"### {data['channel_name']}")
                st.markdown(f'<div class="category-tag">🎯 {data["category"].upper()}</div>', unsafe_allow_html=True)
                st.write(data["description"][:300] + "..." if len(data["description"]) > 300 else data["description"])
                
                creation_date = data["published_at"].split("T")[0] if "T" in data["published_at"] else "N/A"
                st.markdown(f"📅 **Created:** {creation_date} &nbsp;&nbsp;&nbsp; 🌍 **Country:** {data['country']}")

            st.divider()

            # Key Metrics
            benchmark = AUDIENCE_BENCHMARKS.get(data["category"], AUDIENCE_BENCHMARKS["Default"])
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            metrics = [
                ("SUBSCRIBERS", format_number(data["subscribers"]), "total subs"),
                ("TOTAL VIEWS", format_number(data["views"]), "all time"),
                ("VIDEOS", format_number(data["video_count"]), "uploaded"),
                ("MALE %", f"{benchmark['male']}%", "of audience"),
                ("FEMALE %", f"{benchmark['female']}%", "of audience"),
                ("UNDER 18 %", f"{benchmark['under_18']}%", "of audience")
            ]
            
            for i, (label, val, sub) in enumerate(metrics):
                with [m1, m2, m3, m4, m5, m6][i]:
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>{label}</h3>
                        <h1>{val}</h1>
                        <p>{sub}</p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tabs
            tab1, tab2, tab3, tab4 = st.tabs(["👥 Demographics", "📊 Top Videos", "🔥 Engagement", "📅 Distribution"])

            with tab1:
                col_c1, col_c2 = st.columns(2)
                
                with col_c1:
                    st.markdown("#### Gender Breakdown")
                    fig_gender = px.pie(
                        values=[benchmark["male"], benchmark["female"], 100 - (benchmark["male"] + benchmark["female"])],
                        names=["Male", "Female", "Other/Unknown"],
                        color_discrete_sequence=["#60a5fa", "#f472b6", "#94a3b8"],
                        hole=0.4
                    )
                    st.plotly_chart(fig_gender, use_container_width=True)

                with col_c2:
                    st.markdown("#### Age Demographics")
                    age_data = pd.DataFrame({
                        "Age Group": ["Under 18", "18-24", "25-34", "35-44", "45+"],
                        "Percentage": [benchmark["under_18"], 35, 25, 15, 5]
                    })
                    fig_age = px.bar(age_data, x="Age Group", y="Percentage", color_discrete_sequence=["#ff4b4b"])
                    st.plotly_chart(fig_age, use_container_width=True)

                st.markdown("### Audience Insights")
                
                st.markdown(f"""
                <div class="demographic-card male-card">
                    <h4>🧑 Male Audience</h4>
                    <p><b>{benchmark['male']}%</b> of {data['channel_name']}'s audience is male — {benchmark['description']}</p>
                </div>
                <div class="demographic-card female-card">
                    <h4>👩 Female Audience</h4>
                    <p><b>{benchmark['female']}%</b> female viewership. Grow this segment with storytelling-driven content, relatable thumbnails, and community polls.</p>
                </div>
                <div class="demographic-card youth-card">
                    <h4>🧒 Under-18 Reach</h4>
                    <p>~{format_number(float(data['views']) * benchmark['under_18'] / 100)} views from under-18s ({benchmark['under_18']}%). Short hooks, trending audio, and mobile-first editing resonate best with this cohort.</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-note">
                    ℹ️ Demographics are estimated based on the channel's content category ({data['category'].lower()}) using real YouTube audience research benchmarks. 
                    YouTube's API does not expose exact age/gender data publicly — that is only visible to the channel owner inside YouTube Studio.
                </div>
                """, unsafe_allow_html=True)

            with tab2:
                # Fetch recent videos for analysis
                st.markdown("#### Recent Video Performance")
                vid_df = get_videos(data["channel_name"])
                if vid_df is not None and not vid_df.empty:
                    fig_v = px.bar(vid_df, x="title", y="views", color="views", title="Views Distribution")
                    st.plotly_chart(fig_v, use_container_width=True)
                    st.dataframe(vid_df[["title", "views", "likes", "comments", "duration"]], use_container_width=True)
                else:
                    st.info("Harvesting latest videos for performance analysis...")
                    st.button("Click to Fetch Performance Data", key="fetch_v")

            with tab3:
                st.markdown("#### Engagement Levels")
                if vid_df is not None and not vid_df.empty:
                    fig_e = px.scatter(vid_df, x="likes", y="comments", size="views", hover_name="title", title="Interaction Matrix")
                    st.plotly_chart(fig_e, use_container_width=True)
                else:
                    st.warning("No data available. Go to the 'Videos' tab to harvest data first.")

            with tab4:
                st.write("Distribution analysis coming soon...")

        else:
            st.error("Channel not found. Please try another name.")

    st.divider()
    st.info("💡 Enter a channel name above to start your analysis!")

