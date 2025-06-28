import io
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "habits.db"

def get_feelings_for_period(user_id: int, days: int = 30):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT log_date, energy, mood, stress FROM feelings
        WHERE user_id = ? AND log_date >= ?
        ORDER BY log_date ASC
        """, (user_id, (datetime.now() - timedelta(days=days)).date().isoformat()))
        return cursor.fetchall()

def plot_feelings_to_bytes(user_id: int, days: int = 30):
    data = get_feelings_for_period(user_id, days)
    if not data:
        return None

    dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in data]
    energy = [row[1] for row in data]
    mood = [row[2] for row in data]
    stress = [row[3] for row in data]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, energy, label="Энергия", marker='o')
    plt.plot(dates, mood, label="Настроение", marker='o')
    plt.plot(dates, stress, label="Стресс", marker='o')
    plt.xlabel("Дата")
    plt.ylabel("Оценка (0-10)")
    plt.title(f"Твои ощущения за последние {days} дней")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return buf
