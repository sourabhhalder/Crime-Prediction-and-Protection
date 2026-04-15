import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "database.db")

# -------------------------------
# CONNECT DB
# -------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)

# -------------------------------
# CREATE TABLES
# -------------------------------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # Logs table (user predictions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            area TEXT,
            gender TEXT,
            time TEXT,
            safety_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# -------------------------------
# ADD USER
# -------------------------------
def add_user(name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password)
        VALUES (?, ?, ?)
    """, (name, email, password))

    conn.commit()
    conn.close()

# -------------------------------
# VALIDATE USER
# -------------------------------
def validate_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users WHERE email=? AND password=?
    """, (email, password))

    user = cursor.fetchone()
    conn.close()

    return user

# -------------------------------
# SAVE LOG
# -------------------------------
def save_log(email, area, gender, time, score):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO logs (user_email, area, gender, time, safety_score)
        VALUES (?, ?, ?, ?, ?)
    """, (email, area, gender, time, score))

    conn.commit()
    conn.close()

# -------------------------------
# GET USER HISTORY
# -------------------------------
def get_user_logs(email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT area, gender, time, safety_score, timestamp
        FROM logs WHERE user_email=?
        ORDER BY timestamp DESC
    """, (email,))

    data = cursor.fetchall()
    conn.close()

    return data