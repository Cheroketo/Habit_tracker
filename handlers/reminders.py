from aiogram import Dispatcher, types
from models.reminders import set_reminder, delete_reminder

def register_reminder_handlers(dp: Dispatcher):
    @dp.message_handler(commands=["remindme"])
    async def set_remind_time(msg: types.Message):
        await msg.answer("Введи время напоминания (HH:MM):")

    @dp.message_handler(lambda msg: ":" in msg.text and len(msg.text) <= 5)
    async def save_remind_time(msg: types.Message):
        set_reminder(msg.from_user.id, msg.text.strip())
        await msg.answer("Напоминание сохранено 🕒")

    @dp.message_handler(commands=["stopreminder"])
    async def stop_reminder(msg: types.Message):
        delete_reminder(msg.from_user.id)
        await msg.answer("Напоминание отключено ❌")
