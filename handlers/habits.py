from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from models import habits

class AddHabitState(StatesGroup):
    waiting_for_name = State()

def register_habit_handlers(dp: Dispatcher):
    @dp.message_handler(commands=["addhabit"])
    async def add_habit_start(msg: types.Message):
        await msg.answer("Введи название привычки:")
        await AddHabitState.waiting_for_name.set()

    @dp.message_handler(state=AddHabitState.waiting_for_name)
    async def save_habit(msg: types.Message, state: FSMContext):
        habits.add_habit(msg.from_user.id, msg.text.strip())
        await msg.answer("Привычка добавлена ✅")
        await state.finish()

    @dp.message_handler(commands=["list"])
    async def list_habits(msg: types.Message):
        user_habits = habits.get_user_habits(msg.from_user.id)
        if not user_habits:
            await msg.answer("У тебя пока нет привычек.")
            return
        reply = "\n".join([f"{hid}. {name}" for hid, name in user_habits])
        await msg.answer(f"Твои привычки:\n{reply}")

    @dp.message_handler(commands=["done"])
    async def done(msg: types.Message):
        user_habits = habits.get_user_habits(msg.from_user.id)
        if not user_habits:
            await msg.answer("У тебя нет привычек для отметки.")
            return
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for hid, name in user_habits:
            keyboard.add(f"{hid}. {name}")
        await msg.answer("Выбери привычку для отметки:", reply_markup=keyboard)

    @dp.message_handler(lambda msg: "." in msg.text)
    async def mark_done(msg: types.Message):
        try:
            habit_id = int(msg.text.split(".")[0])
            success = habits.log_habit(habit_id)
            if success:
                await msg.answer("Отмечено ✅", reply_markup=types.ReplyKeyboardRemove())
            else:
                await msg.answer("Ты уже отмечал эту привычку сегодня 🤓", reply_markup=types.ReplyKeyboardRemove())
        except:
            await msg.answer("Неверный формат. Попробуй снова.")

    @dp.message_handler(commands=["today"])
    async def today_done(msg: types.Message):
        logs = habits.get_today_logs(msg.from_user.id)
        if logs:
            await msg.answer("Сегодня ты сделал:\n" + "\n".join(logs))
        else:
            await msg.answer("Ты пока ничего не отметил сегодня 😴")