from .db import get_connection
from datetime import datetime

def create_habits_table():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")

def create_habit_logs_table():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )""")

def add_habit(user_id: int, name: str):
    with get_connection() as conn:
        conn.execute("""
        INSERT INTO habits (user_id, name, created_at)
        VALUES (?, ?, ?)""",
        (user_id, name, datetime.now().isoformat()))

def log_habit(habit_id: int):
    today = datetime.now().date().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 1 FROM habit_logs
        WHERE habit_id = ? AND log_date = ?""", (habit_id, today))
        if cursor.fetchone():
            return False  # Уже отмечено
        cursor.execute("""
        INSERT INTO habit_logs (habit_id, log_date)
        VALUES (?, ?)""", (habit_id, today))
        return True

def get_user_habits(user_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT id, name FROM habits WHERE user_id = ?", (user_id,)).fetchall()

def get_today_logs(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT h.name FROM habit_logs l
        JOIN habits h ON h.id = l.habit_id
        WHERE h.user_id = ? AND l.log_date = ?""",
        (user_id, datetime.now().date().isoformat()))
        return [row[0] for row in cursor.fetchall()]
