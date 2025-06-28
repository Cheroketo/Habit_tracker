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
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS feelings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    log_date TEXT NOT NULL,
                    energy INTEGER,
                    mood INTEGER,
                    stress INTEGER,
                    note TEXT
                )
                """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    user_id INTEGER PRIMARY KEY,
                    time TEXT NOT NULL
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

def log_feelings(user_id: int, energy: int, mood: int, stress: int, note: str = ""):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO feelings (user_id, log_date, energy, mood, stress, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, datetime.now().date().isoformat(), energy, mood, stress, note))
        conn.commit()


def get_average_feelings(user_id: int, days: int = 7):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT AVG(energy), AVG(mood), AVG(stress)
            FROM feelings
            WHERE user_id = ? AND log_date >= date('now', ?)
        """, (user_id, f'-{days} day'))
        return cursor.fetchone()

def get_habit_stats(user_id: int, habit_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Проверка, что привычка принадлежит юзеру
        cursor.execute("SELECT name FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
        habit = cursor.fetchone()
        if not habit:
            return None

        habit_name = habit[0]

        # Кол-во дней, когда привычка была выполнена
        cursor.execute("""
            SELECT COUNT(DISTINCT log_date) FROM habit_logs
            WHERE habit_id = ?
        """, (habit_id,))
        days_done = cursor.fetchone()[0]

        # Кол-во дней с отметками пользователя (для процента)
        cursor.execute("""
            SELECT COUNT(DISTINCT log_date) FROM habit_logs l
            JOIN habits h ON l.habit_id = h.id
            WHERE h.user_id = ?
        """, (user_id,))
        total_days = cursor.fetchone()[0]

        pct = (days_done / total_days * 100) if total_days else 0

        return habit_name, days_done, total_days, pct


def set_reminder_time(user_id: int, time_str: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reminders (user_id, time)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET time=excluded.time
        """, (user_id, time_str))
        conn.commit()


