from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import TOKEN
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import models
from analytics import plot_feelings_to_bytes


class FeelingsState(StatesGroup):
    waiting_for_energy = State()
    waiting_for_mood = State()
    waiting_for_stress = State()
    waiting_for_note = State()


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

models.create_tables()

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("Привет! Я твой трекер привычек.\n\nДоступные команды:\n/add — добавить привычку"
                     "\n/list — список привычек\n/done — отметить выполнение\
                    \n/today — что ты выполнил сегодня"
                     "\n/feelings — записывай свои ощущения каждый день"
                     "\n/mystats — Показывает средние показатели твоих ощущений (энергия, настроение, стресс) за последние 7 дней"
                     "\n/habitstats <id>: информация расширенная по привычке "
                     "\n/graph - построения графиков по твоему состоянию")

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

@dp.message_handler(commands=['feelings'])
async def feelings_start(msg: types.Message):
    await msg.answer("Оцени свою энергию от 0 до 10:")
    await FeelingsState.waiting_for_energy.set()

@dp.message_handler(state=FeelingsState.waiting_for_energy)
async def feelings_energy(msg: types.Message, state: FSMContext):
    await state.update_data(energy=int(msg.text))
    await msg.answer("Теперь оцени настроение от 0 до 10:")
    await FeelingsState.waiting_for_mood.set()

@dp.message_handler(state=FeelingsState.waiting_for_mood)
async def feelings_mood(msg: types.Message, state: FSMContext):
    await state.update_data(mood=int(msg.text))
    await msg.answer("Теперь оцени стресс от 0 до 10:")
    await FeelingsState.waiting_for_stress.set()

@dp.message_handler(state=FeelingsState.waiting_for_stress)
async def feelings_stress(msg: types.Message, state: FSMContext):
    await state.update_data(stress=int(msg.text))
    await msg.answer("Хочешь что-то добавить? (Напиши или '-' если нет)")
    await FeelingsState.waiting_for_note.set()

@dp.message_handler(state=FeelingsState.waiting_for_note)
async def feelings_note(msg: types.Message, state: FSMContext):
    note = msg.text if msg.text != "-" else ""
    data = await state.get_data()

    models.log_feelings(
        user_id=msg.from_user.id,
        energy=data['energy'],
        mood=data['mood'],
        stress=data['stress'],
        note=note
    )

    await msg.answer("Чувства записаны! 🧠", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(commands=['mystats'])
async def mystats(msg: types.Message):
    avg = models.get_average_feelings(msg.from_user.id)
    if not any(avg):
        await msg.answer("Недостаточно данных для статистики. Запиши ощущения через /feelings.")
        return
    energy, mood, stress = avg
    response = (
        f"Средние показатели за последние 7 дней:\n"
        f"⚡ Энергия: {energy:.1f}\n"
        f"😊 Настроение: {mood:.1f}\n"
        f"😰 Стресс: {stress:.1f}"
    )
    await msg.answer(response)


@dp.message_handler(commands=['habitstats'])
async def habitstats(msg: types.Message):
    args = msg.get_args()
    habits = models.get_user_habits(msg.from_user.id)
    if not habits:
        await msg.answer("У тебя пока нет привычек. Добавь их командой /add")
        return

    if not args:
        keyboard = InlineKeyboardMarkup(row_width=1)
        for habit_id, habit_name in habits:
            keyboard.add(InlineKeyboardButton(text=habit_name, callback_data=f"habitstats_{habit_id}"))
        await msg.answer("Выбери привычку, чтобы посмотреть статистику:", reply_markup=keyboard)
        return

    if args.isdigit():
        habit_id = int(args)
        await send_habit_stats(msg, habit_id)
    else:
        await msg.answer("Использование: /habitstats <id> или просто /habitstats для выбора из списка.")

async def send_habit_stats(event, habit_id: int):
    # Определяем user_id
    if hasattr(event, 'from_user'):
        user_id = event.from_user.id
    elif hasattr(event, 'message') and event.message.from_user:
        user_id = event.message.from_user.id
    else:
        return

    stats = models.get_habit_stats(user_id, habit_id)
    if not stats:
        # Отправляем сообщение в зависимости от типа event
        if hasattr(event, 'answer') and callable(event.answer):  # CallbackQuery
            await event.answer("Привычка с таким ID не найдена.")
        else:  # Message
            await event.answer("Привычка с таким ID не найдена.")
        return

    habit_name, days_done, total_days, pct = stats
    response = (
        f"Статистика по привычке «{habit_name}»:\n"
        f"Выполнена в {days_done} днях из {total_days} ({pct:.1f}%)"
    )

    # Отправляем ответ в зависимости от типа event
    if hasattr(event, 'message') and hasattr(event.message, 'answer'):  # CallbackQuery
        await event.message.answer(response)
    elif hasattr(event, 'answer'):  # Message
        await event.answer(response)
    else:
        # На всякий случай — ничего не делать
        pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('habitstats_'))
async def process_habitstats_callback(callback_query: types.CallbackQuery):
    habit_id = int(callback_query.data.split('_')[1])
    await send_habit_stats(callback_query, habit_id)
    await callback_query.answer()


@dp.message_handler(commands=['graph'])
async def graph(msg: types.Message):
    img_buf = plot_feelings_to_bytes(msg.from_user.id)
    if img_buf is None:
        await msg.answer("Нет данных для построения графика.")
        return

    await msg.answer_photo(photo=img_buf, caption="Твои ощущения за месяц")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
