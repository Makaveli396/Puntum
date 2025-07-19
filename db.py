import sqlite3
from datetime import datetime

DB_PATH = "puntum.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS points (
            user_id INTEGER,
            username TEXT,
            points INTEGER,
            hashtag TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            chat_id INTEGER,
            message_id INTEGER,
            is_challenge_bonus INTEGER DEFAULT 0
        )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS user_achievements (
            user_id INTEGER,
            achievement_id INTEGER,
            date TEXT DEFAULT CURRENT_DATE,
            PRIMARY KEY (user_id, achievement_id)
        )"""
    )

    conn.commit()
    conn.close()

def add_points(user_id, username, points, hashtag=None, message_text=None, chat_id=None, message_id=None, is_challenge_bonus=False, context=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO points (user_id, username, points, hashtag, chat_id, message_id, is_challenge_bonus)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, username, points, hashtag, chat_id, message_id, int(is_challenge_bonus))
    )

    conn.commit()
    conn.close()

    if context and chat_id:
        from handlers.achievements import check_achievements
        check_achievements(user_id, username, context, chat_id)

    return {"ok": True}

def add_achievement(user_id: int, achievement_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR IGNORE INTO user_achievements (user_id, achievement_id)
           VALUES (?, ?)""",
        (user_id, achievement_id)
    )
    conn.commit()
    conn.close()

def get_user_stats(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT hashtag, COUNT(*) FROM points
           WHERE user_id = ?
           GROUP BY hashtag""",
        (user_id,)
    )
    hashtag_counts = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute(
        """SELECT DISTINCT DATE(timestamp) FROM points
           WHERE user_id = ?""",
        (user_id,)
    )
    active_days = {row[0] for row in cursor.fetchall()}

    cursor.execute(
        """SELECT COUNT(*) FROM points
           WHERE user_id = ? AND is_challenge_bonus = 1
           AND hashtag = '(reto_diario)'
           AND strftime('%W', timestamp) = strftime('%W', 'now')""",
        (user_id,)
    )
    daily_challenges_week = cursor.fetchone()[0]

    cursor.execute(
        """SELECT 1 FROM points
           WHERE user_id = ? AND is_challenge_bonus = 1
           AND hashtag LIKE '#%' AND strftime('%W', timestamp) = strftime('%W', 'now')
           LIMIT 1""",
        (user_id,)
    )
    weekly_done = bool(cursor.fetchone())

    cursor.execute(
        """SELECT achievement_id FROM user_achievements
           WHERE user_id = ?""",
        (user_id,)
    )
    achievements = [row[0] for row in cursor.fetchall()]

    conn.close()
    return {
        "hashtag_counts": hashtag_counts,
        "active_days": active_days,
        "daily_challenges_week": daily_challenges_week,
        "weekly_challenge_done": weekly_done,
        "achievements": achievements
    }