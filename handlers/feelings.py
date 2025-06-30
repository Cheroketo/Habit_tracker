
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import Dispatcher

from models.feelings import log_feelings

class FeelingsState(StatesGroup):
    waiting_for_energy = State()
    waiting_for_mood = State()
    waiting_for_stress = State()
    waiting_for_note = State()

# Команда /feelings
async def cmd_feelings(msg: types.Message):
    await msg.answer("Оцени свою энергию от 1 до 10")
    await FeelingsState.waiting_for_energy.set()

# Шаг 1 — энергия
async def process_energy(msg: types.Message, state: FSMContext):
    try:
        energy = int(msg.text)
        if not 1 <= energy <= 10:
            raise ValueError
    except ValueError:
        return await msg.answer("Пожалуйста, введи число от 1 до 10")

    await state.update_data(energy=energy)
    await msg.answer("Теперь оцени настроение от 1 до 10")
    await FeelingsState.waiting_for_mood.set()

# Шаг 2 — настроение
async def process_mood(msg: types.Message, state: FSMContext):
    try:
        mood = int(msg.text)
        if not 1 <= mood <= 10:
            raise ValueError
    except ValueError:
        return await msg.answer("Пожалуйста, введи число от 1 до 10")

    await state.update_data(mood=mood)
    await msg.answer("Теперь оцени уровень стресса от 1 до 10")
    await FeelingsState.waiting_for_stress.set()

# Шаг 3 — стресс
async def process_stress(msg: types.Message, state: FSMContext):
    try:
        stress = int(msg.text)
        if not 1 <= stress <= 10:
            raise ValueError
    except ValueError:
        return await msg.answer("Пожалуйста, введи число от 1 до 10")

    await state.update_data(stress=stress)
    await msg.answer("Хочешь добавить комментарий? Напиши его, либо напиши 'нет'")
    await FeelingsState.waiting_for_note.set()

# Шаг 4 — комментарий
async def process_note(msg: types.Message, state: FSMContext):
    note = msg.text if msg.text.lower() != "нет" else ""
    data = await state.get_data()
    log_feelings(
        user_id=msg.from_user.id,
        energy=data["energy"],
        mood=data["mood"],
        stress=data["stress"],
        note=note
    )
    await msg.answer("✅ Ощущения на сегодня сохранены. Спасибо!")
    await state.finish()


def register_feelings_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_feelings, commands=["feelings"], state="*")
    dp.register_message_handler(process_energy, state=FeelingsState.waiting_for_energy)
    dp.register_message_handler(process_mood, state=FeelingsState.waiting_for_mood)
    dp.register_message_handler(process_stress, state=FeelingsState.waiting_for_stress)
    dp.register_message_handler(process_note, state=FeelingsState.waiting_for_note)