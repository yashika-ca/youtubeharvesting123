import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def show_graph(channel_name):
    try:
        conn = sqlite3.connect("Youtube.db")
        
        # Pull the columns we need
        query = """
        SELECT channel, video_id, title, views, likes, comments, duration
        FROM Youtube
        WHERE channel COLLATE NOCASE = ?
        """
        
        df = pd.read_sql(query, conn, params=(channel_name,))
    except Exception:
        df = pd.DataFrame()
    finally:
        if 'conn' in locals():
            conn.close()

    if df.empty:
        st.warning("No videos found for this channel. Fetch data first from the Analytics or Videos tab.")
        return

    # Create Radial Tree Logic
    # -------------------------
    node_x = []
    node_y = []
    hover_text = []
    display_text = []
    node_color = []
    node_size = []
    text_position = []
    
    edge_x = []
    edge_y = []

    # 1. Central Node
    node_x.append(0)
    node_y.append(0)
    display_text.append(f"<b>{channel_name}</b>")
    hover_text.append(f"Channel: {channel_name}")
    node_color.append('#ffffff') # White center
    node_size.append(35)
    text_position.append("bottom center")
    
    # 2. Videos and Metrics
    n_videos = len(df)
    
    # Predefined color palette for branches
    branch_colors = ['#00e5ff', '#00ff88', '#ffea00', '#ff2a55', '#bb33ff', '#3366ff', '#ff33aa']
    
    # Adjust outer radius based on number of videos to give more breathing room
    r_v = 1.0
    r_m = 1.7 if n_videos <= 10 else 2.5
    
    for i, row in df.iterrows():
        # Video Base Angle
        theta_v = i * (2 * np.pi / n_videos)
        
        x_v = r_v * np.cos(theta_v)
        y_v = r_v * np.sin(theta_v)
        
        # Add Video Node
        title = row['title']
        title_short = title[:20] + "..." if len(title) > 20 else title
        node_x.append(x_v)
        node_y.append(y_v)
        display_text.append(title_short)
        hover_text.append(f"Video: {title}")
        
        v_color = branch_colors[i % len(branch_colors)]
        
        node_color.append(v_color)
        node_size.append(18)
        
        # Smart text positioning based on quadrant
        if x_v > 0 and y_v > 0: pos = "top right"
        elif x_v < 0 and y_v > 0: pos = "top left"
        elif x_v < 0 and y_v < 0: pos = "bottom left"
        else: pos = "bottom right"
        text_position.append(pos)
        
        # Edge: Center -> Video
        edge_x.extend([0, x_v, None])
        edge_y.extend([0, y_v, None])
        
        # 3. Metrics for this Video
        def fmt(val):
            if pd.isna(val) or val is None or val == "": return "0"
            try:
                v = int(val)
                if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
                if v >= 1_000: return f"{v/1_000:.1f}K"
                return str(v)
            except:
                return str(val)

        metrics = [
            ("Views", fmt(row['views'])),
            ("Likes", fmt(row['likes'])),
            ("Comments", fmt(row['comments'])),
            ("Duration", str(row['duration']))
        ]
        
        n_metrics = len(metrics)
        
        # Spread angle constraints
        spread = (2 * np.pi / n_videos) * 0.75 
        start_theta = theta_v - (spread / 2)
        step = spread / (n_metrics - 1) if n_metrics > 1 else 0
        
        for j, (m_label, m_val) in enumerate(metrics):
            theta_m = start_theta + j * step
            x_m = r_m * np.cos(theta_m)
            y_m = r_m * np.sin(theta_m)
            
            # Add Metric Node
            node_x.append(x_m)
            node_y.append(y_m)
            # The outer ring has label + value
            display_text.append(f"{m_label}: {m_val}")
            hover_text.append(f"{m_label}: {m_val}")
            
            # Dimmer node color for leaves, or same color
            node_color.append(v_color)
            node_size.append(8)
            
            # Determine text position for leaves exactly expanding outwards
            if np.cos(theta_m) >= 0:
                text_position.append("middle right")
            else:
                text_position.append("middle left")
            
            # Edge: Video -> Metric
            edge_x.extend([x_v, x_m, None])
            edge_y.extend([y_v, y_m, None])

    # Plotting
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color='#444'),
        hoverinfo='none',
        mode='lines'
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=display_text,
        hovertext=hover_text,
        hoverinfo='text',
        textposition=text_position,
        textfont=dict(color='white', size=11),
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line_width=1,
            line_color='white'
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=20,r=20,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=700
             ))
             
    fig.update_layout(
        template="plotly_dark",
        dragmode="pan"
    )

    st.write(f"### 🔗 Radial Interaction Network for {channel_name}")
    st.write("Zoom and pan to explore video metrics like Views, Likes, and Comments.")
    st.plotly_chart(fig, use_container_width=True)
