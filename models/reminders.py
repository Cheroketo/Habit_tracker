from .db import get_connection

def create_reminders_table():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            user_id INTEGER PRIMARY KEY,
            time TEXT
        )""")

def set_reminder(user_id: int, time: str):
    with get_connection() as conn:
        conn.execute("""
        INSERT OR REPLACE INTO reminders (user_id, time) VALUES (?, ?)""",
        (user_id, time))

def get_reminder_time(user_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT time FROM reminders WHERE user_id = ?", (user_id,)).fetchone()
        return row[0] if row else None

def delete_reminder(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))