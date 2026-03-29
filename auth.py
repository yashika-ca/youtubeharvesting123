import streamlit as st
import sqlite3
import pandas as pd
from streamlit_option_menu import option_menu

def init_db():
    conn = sqlite3.connect("Youtube.db")
    cursor = conn.cursor()
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

def signup_user(name, email, password):
    try:
        conn = sqlite3.connect("Youtube.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        conn.close()
        return True, "Account created successfully. Please login using the Login page."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    except Exception as e:
        return False, f"Error: {e}"

def login_user(email, password):
    try:
        conn = sqlite3.connect("Youtube.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, password FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return True, user[0]
        else:
            return False, "Invalid email or password."
    except Exception as e:
        return False, f"Error: {e}"

def show_auth_ui():
    init_db()
    
    with st.sidebar:
        # Professional header to match Image 1
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 12px; padding-bottom: 5px;">
                <img src="https://cdn-icons-png.flaticon.com/512/1384/1384060.png" width="35">
                <h2 style="margin: 0; font-size: 26px; color: white;">Auth</h2>
            </div>
            <hr style="margin: 10px 0 25px 0; border: none; border-top: 1px solid #444;">
        """, unsafe_allow_html=True)
        
        auth_mode = option_menu(
            None,
            ["Login", "Signup"],
            icons=["box-arrow-in-right", "person-plus"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "white", "font-size": "20px"}, 
                "nav-link": {
                    "font-size": "18px", 
                    "text-align": "left", 
                    "margin": "0px", 
                    "color": "white",
                    "padding": "12px 20px"
                },
                "nav-link-selected": {
                    "background-color": "#ff4b4b",
                    "font-weight": "600"
                },
            }
        )

    if auth_mode == "Signup":
        st.title("📝 Create Account")
        with st.form("signup_form"):
            name = st.text_input("Name")
            email = st.text_input("Email ID")
            password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Signup")
            
            if submit:
                if not name or not email or not password:
                    st.error("Please fill all fields.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = signup_user(name, email, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    elif auth_mode == "Login":
        st.title("🔑 Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not email or not password:
                    st.error("Please fill all fields.")
                else:
                    success, username = login_user(email, password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.success(f"Welcome, {username}")
                        st.rerun()
                    else:
                        st.error(username)
