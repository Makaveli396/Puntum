import sqlite3

conn = sqlite3.connect("cinebot.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, points INTEGER, count INTEGER)")
conn.commit()

def add_points(user_id, username, pts):
    cur.execute("SELECT points, count FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET points=points+?, count=count+1 WHERE id=?", (pts, user_id))
    else:
        cur.execute("INSERT INTO users (id, username, points, count) VALUES (?, ?, ?, 1)", (user_id, username, pts))
    conn.commit()

def get_user_stats(user_id):
    cur.execute("SELECT username, points, count FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if row:
        return {"username": row[0], "points": row[1], "count": row[2]}
    return None

def get_top10():
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    return cur.fetchall()

def set_challenge(text): pass  # opcional
