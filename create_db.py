import sqlite3

conn = sqlite3.connect("Youtube.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS Youtube")

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

print("Database created successfully")
