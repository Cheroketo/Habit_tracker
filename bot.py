import logging
import sqlite3
import re
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage


import models
from models import create_tables, add_habit, get_user_habits, log_habit, get_today_logs, set_reminder_time, get_habit_stats
from analytics import plot_feelings_to_bytes
from scheduler import start_scheduler, schedule_user_reminder, scheduler
from config import TOKEN
from aiogram.dispatcher import FSMContext




API_TOKEN = TOKEN  # замените на ваш токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# === Стартовая команда ===
@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message):
    await msg.answer("Привет! Я — твой трекер привычек и помощник. Используй /addhabit, /done, /today, /feelings, /graph и /remindme HH:MM")

# === Добавление привычки ===
@dp.message_handler(commands=['addhabit'])
async def addhabit(msg: types.Message):
    args = msg.get_args()
    if not args:
        await msg.answer("Напиши название привычки после команды. Например: /addhabit Зарядка")
        return
    add_habit(msg.from_user.id, args.strip())
    await msg.answer(f"Привычка '{args.strip()}' добавлена ✅")

# === Отметить привычку как выполненную ===
@dp.message_handler(commands=['done'])
async def done(msg: types.Message):
    habits = get_user_habits(msg.from_user.id)
    if not habits:
        await msg.answer("У тебя нет привычек. Добавь через /addhabit")
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for h in habits:
        keyboard.add(h[1])
    await msg.answer("Выбери привычку, которую выполнил:", reply_markup=keyboard)
    await dp.current_state(user=msg.from_user.id).set_state("waiting_for_done")

@dp.message_handler(state="waiting_for_done")
async def handle_done(msg: types.Message):
    habits = get_user_habits(msg.from_user.id)
    selected = msg.text.strip()
    habit_dict = {name: hid for hid, name in habits}
    if selected not in habit_dict:
        await msg.answer("Не понял. Попробуй ещё раз.")
        return
    result = log_habit(habit_dict[selected])
    if result:
        await msg.answer("Отмечено как выполнено ✅", reply_markup=types.ReplyKeyboardRemove())
    else:
        await msg.answer("Ты уже отмечал эту привычку сегодня 😉", reply_markup=types.ReplyKeyboardRemove())
    await dp.current_state(user=msg.from_user.id).finish()

# === Посмотреть привычки за сегодня ===
@dp.message_handler(commands=['today'])
async def today(msg: types.Message):
    done = get_today_logs(msg.from_user.id)
    if not done:
        await msg.answer("Сегодня ещё ничего не отмечено ❌")
    else:
        await msg.answer("Сегодня ты выполнил:" + "\n".join(f"✅ {h}" for h in done))

# === График ощущений ===
@dp.message_handler(commands=['graph'])
async def graph(msg: types.Message):
    img_buf = plot_feelings_to_bytes(msg.from_user.id)
    if img_buf is None:
        await msg.answer("Нет данных для построения графика. Запиши ощущения через /feelings.")
        return
    await msg.answer_photo(photo=img_buf, caption="Вот твои ощущения за последний месяц.")

@dp.message_handler(commands=['list'])
async def list_habits(msg: types.Message):
    habits = get_user_habits(msg.from_user.id)
    if not habits:
        await msg.answer("У тебя пока нет привычек. Добавь через /addhabit")
        return
    text = "Твои привычки:\n"
    for hid, name in habits:
        text += f"- {name} (ID: {hid})\n"
    await msg.answer(text)

@dp.message_handler(commands=['mystats'])
async def mystats(msg: types.Message):
    args = msg.get_args().strip()
    if not args.isdigit():
        await msg.answer("Напиши команду так: /mystats ID_привычки\nНапример: /mystats 2")
        return
    habit_id = int(args)

    result = get_habit_stats(msg.from_user.id, habit_id)
    if not result:
        await msg.answer("Привычка с таким ID не найдена или она не твоя.")
        return

    habit_name, days_done, total_days, pct = result
    await msg.answer(f"Статистика по привычке «{habit_name}»:\n"
                     f"Выполнена в {days_done} днях из {total_days} ({pct:.1f}%)")


# === Установить напоминание ===
@dp.message_handler(commands=['remindme'])
async def remindme(msg: types.Message):
    args = msg.get_args().strip()
    if not re.match(r"^\d{1,2}:\d{2}$", args):
        await msg.answer("Формат времени: /remindme HH:MM, например: /remindme 21:00")
        return
    hour, minute = map(int, args.split(":"))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        await msg.answer("Некорректное время. Введи в формате от 00:00 до 23:59")
        return
    set_reminder_time(msg.from_user.id, args)
    schedule_user_reminder(msg.from_user.id, bot)
    await msg.answer(f"🔔 Напоминание установлено на {args}.")

# === Отключить напоминание ===
@dp.message_handler(commands=['stopreminder'])
async def stop_reminder(msg: types.Message):
    user_id = msg.from_user.id
    job_id = f"reminder_{user_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    with sqlite3.connect(models.DB_NAME) as conn:
        conn.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        conn.commit()
    await msg.answer("🔕 Напоминание отключено.")


from aiogram.dispatcher.filters.state import StatesGroup, State

class FeelingsForm(StatesGroup):
    energy = State()
    mood = State()
    stress = State()
    note = State()

@dp.message_handler(commands=['feelings'])
async def feelings_start(msg: types.Message):
    await msg.answer("Оцени свою *энергию* от 1 до 10:")
    await FeelingsForm.energy.set()



@dp.message_handler(state=FeelingsForm.energy)
async def process_energy(msg: types.Message, state: FSMContext):
    try:
        val = int(msg.text)
        if val < 1 or val > 10:
            raise ValueError()
    except:
        await msg.answer("Пожалуйста, введи число от 1 до 10 для энергии.")
        return
    await state.update_data(energy=val)
    await msg.answer("Теперь оцени своё *настроение* от 1 до 10:")
    await FeelingsForm.next()  # mood

@dp.message_handler(state=FeelingsForm.mood)
async def process_mood(msg: types.Message, state: FSMContext):
    try:
        val = int(msg.text)
        if val < 1 or val > 10:
            raise ValueError()
    except:
        await msg.answer("Пожалуйста, введи число от 1 до 10 для настроения.")
        return
    await state.update_data(mood=val)
    await msg.answer("Оцени уровень *стресса* от 1 до 10:")
    await FeelingsForm.next()  # stress

@dp.message_handler(state=FeelingsForm.stress)
async def process_stress(msg: types.Message, state: FSMContext):
    try:
        val = int(msg.text)
        if val < 1 or val > 10:
            raise ValueError()
    except:
        await msg.answer("Пожалуйста, введи число от 1 до 10 для стресса.")
        return
    await state.update_data(stress=val)
    await msg.answer("Если хочешь, можешь добавить заметку или напиши 'нет':")
    await FeelingsForm.next()  # note

@dp.message_handler(state=FeelingsForm.note)
async def process_note(msg: types.Message, state: FSMContext):
    note_text = msg.text.strip()
    if note_text.lower() == 'нет':
        note_text = ""

    data = await state.get_data()
    energy = data['energy']
    mood = data['mood']
    stress = data['stress']

    # Запись в базу
    models.log_feelings(msg.from_user.id, energy, mood, stress, note_text)

    await msg.answer("Спасибо! Твои ощущения записаны ✅")
    await state.finish()


@dp.message_handler(commands=['help'])
async def help_cmd(msg: types.Message):
    text = (
        "📝 *Трекер привычек — что умеет бот:*\n\n"
        "/addhabit Название — добавить новую привычку\n"
        "/list — показать список твоих привычек\n"
        "/done — отметить привычку как выполненную сегодня\n"
        "/today — показать, что ты выполнил сегодня\n"
        "/feelings — записать свои ощущения (по шкале 1–10)\n"
        "/graph — показать график твоих ощущений за месяц\n"
        "/mystats ID — показать статистику по привычке (например, /mystats 2)\n"
        "/remindme HH:MM — установить ежедневное напоминание (например, /remindme 21:00)\n"
        "/stopreminder — отключить напоминания\n"
        "/help — показать это сообщение\n\n"
        "Если хочешь, просто пиши команды, я помогу!"
    )
    await msg.answer(text, parse_mode='Markdown')


async def on_startup(dp):
    start_scheduler()
    # Запланировать напоминания для всех пользователей
    with sqlite3.connect("habits.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM reminders")
        for row in cursor.fetchall():
            schedule_user_reminder(row[0], bot)

if __name__ == '__main__':
    create_tables()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)