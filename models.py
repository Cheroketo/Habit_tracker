import sqlite3
from datetime import datetime

DB_NAME = "habits.db"

def create_tables():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )
        """)
        conn.commit()


def add_habit(user_id: int, name: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO habits (user_id, name, created_at)
        VALUES (?, ?, ?)
        """, (user_id, name, datetime.now().isoformat()))
        conn.commit()


def get_user_habits(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, name FROM habits WHERE user_id = ?
        """, (user_id,))
        return cursor.fetchall()


def log_habit(habit_id: int) -> bool:
    today = datetime.now().date().isoformat()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id FROM habit_logs
        WHERE habit_id = ? AND log_date = ?
        """, (habit_id, today))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
            INSERT INTO habit_logs (habit_id, log_date)
            VALUES (?, ?)
            """, (habit_id, today))
            conn.commit()
            return True
        else:
            return False


def get_today_logs(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT h.name FROM habit_logs l
        JOIN habits h ON h.id = l.habit_id
        WHERE h.user_id = ? AND l.log_date = ?
        """, (user_id, datetime.now().date().isoformat()))
        return [row[0] for row in cursor.fetchall()]

