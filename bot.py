from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import models
import os

from config import TOKEN

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

models.create_tables()

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("Привет! Я твой трекер привычек.\n\nДоступные команды:\n/add — добавить привычку\n/list — список привычек\n/done — отметить выполнение\n/today — что ты выполнил сегодня")

@dp.message_handler(commands=['add'])
async def add(msg: types.Message):
    await msg.answer("Введи название привычки:")
    await dp.current_state(user=msg.from_user.id).set_state("waiting_for_habit")

@dp.message_handler(state="waiting_for_habit")
async def habit_name(msg: types.Message):
    models.add_habit(msg.from_user.id, msg.text)
    await msg.answer(f"Привычка «{msg.text}» добавлена!")
    await dp.current_state(user=msg.from_user.id).reset_state()

@dp.message_handler(commands=['list'])
async def list_habits(msg: types.Message):
    habits = models.get_user_habits(msg.from_user.id)
    if not habits:
        await msg.answer("У тебя пока нет привычек. Добавь их с помощью /add")
        return
    response = "Твои привычки:\n"
    for habit in habits:
        response += f"• {habit[1]} (id: {habit[0]})\n"
    await msg.answer(response)

@dp.message_handler(commands=['done'])
async def done(msg: types.Message):
    habits = models.get_user_habits(msg.from_user.id)
    if not habits:
        await msg.answer("Нет привычек для отметки. Добавь их с помощью /add")
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for habit in habits:
        keyboard.add(KeyboardButton(f"{habit[1]} ({habit[0]})"))
    await msg.answer("Выбери привычку для отметки как выполненную:", reply_markup=keyboard)
    await dp.current_state(user=msg.from_user.id).set_state("waiting_for_done")

@dp.message_handler(state="waiting_for_done")
async def mark_done(msg: types.Message):
    try:
        habit_id = int(msg.text.strip().split('(')[-1][:-1])
        result = models.log_habit(habit_id)  # ← добавили проверку

        if result:
            await msg.answer("Отмечено как выполнено ✅", reply_markup=types.ReplyKeyboardRemove())
        else:
            await msg.answer("Ты уже отмечал эту привычку сегодня 😉", reply_markup=types.ReplyKeyboardRemove())

    except Exception:
        await msg.answer("Не удалось отметить. Убедись, что выбрал из списка.")
    finally:
        await dp.current_state(user=msg.from_user.id).reset_state()



@dp.message_handler(commands=['today'])
async def today(msg: types.Message):
    logs = models.get_today_logs(msg.from_user.id)
    if not logs:
        await msg.answer("Сегодня ты ещё ничего не отметил.")
        return
    response = "Сегодня ты выполнил:\n"
    response += "\n".join(f"✅ {habit}" for habit in logs)
    await msg.answer(response)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
