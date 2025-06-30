from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN

from handlers.general import register_general_handlers
from handlers.habits import register_habit_handlers
from handlers.feelings import register_feelings_handlers
from handlers.reminders import register_reminder_handlers
from handlers.analytics import register_analytics_handlers  # Новый импорт

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

register_general_handlers(dp)
register_habit_handlers(dp)
register_feelings_handlers(dp)
register_reminder_handlers(dp)
register_analytics_handlers(dp)  # Регистрация

if __name__ == "__main__":
    from models.db import create_all_tables
    create_all_tables()
    executor.start_polling(dp, skip_updates=True)
