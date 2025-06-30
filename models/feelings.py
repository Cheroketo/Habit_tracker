from datetime import datetime
from .db import get_connection

def create_feelings_table():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS feelings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            energy INTEGER,
            mood INTEGER,
            stress INTEGER,
            note TEXT
        )""")

def log_feelings(user_id: int, energy: int, mood: int, stress: int, note: str = ""):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO feelings (user_id, log_date, energy, mood, stress, note)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, datetime.now().date().isoformat(), energy, mood, stress, note))

def get_feelings_by_user(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT log_date, energy, mood, stress FROM feelings WHERE user_id = ? ORDER BY log_date", (user_id,))
        rows = cursor.fetchall()
        return [
            {"log_date": row[0], "energy": row[1], "mood": row[2], "stress": row[3]}
            for row in rows
        ]
