import sqlite3
from config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_all_tables():
    from models.habits import create_habits_table, create_habit_logs_table
    from models.feelings import create_feelings_table
    from models.reminders import create_reminders_table
    create_habits_table()
    create_habit_logs_table()
    create_feelings_table()
    create_reminders_table()
