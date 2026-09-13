import sqlite3
from datetime import datetime
import pandas as pd

DB_NAME = "lifelens.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            app_name TEXT NOT NULL,
            window_title TEXT,
            category TEXT NOT NULL,
            duration_seconds REAL DEFAULT 0,
            idle_seconds REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_seconds REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def add_activity(
    app_name,
    window_title,
    category,
    duration_seconds,
    idle_seconds
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO activity
        (
            timestamp,
            app_name,
            window_title,
            category,
            duration_seconds,
            idle_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        app_name,
        window_title,
        category,
        duration_seconds,
        min(duration_seconds, idle_seconds)
    ))

    conn.commit()
    conn.close()


def get_activity():
    conn = get_connection()

    try:
        return pd.read_sql_query("""
            SELECT
                id,
                timestamp,
                app_name,
                window_title,
                category,
                duration_seconds,
                idle_seconds
            FROM activity
            ORDER BY timestamp ASC
        """, conn)

    finally:
        conn.close()


def get_today_activity():
    conn = get_connection()

    today = datetime.now().strftime("%Y-%m-%d")

    try:
        return pd.read_sql_query("""
            SELECT
                id,
                timestamp,
                app_name,
                window_title,
                category,
                duration_seconds,
                idle_seconds
            FROM activity
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp ASC
        """, conn, params=(today,))

    finally:
        conn.close()


def delete_all_activity():
    conn = get_connection()

    conn.execute("DELETE FROM activity")
    conn.execute("DELETE FROM focus_sessions")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")