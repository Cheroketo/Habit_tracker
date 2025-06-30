
from aiogram import types
from aiogram.dispatcher import Dispatcher
from models.feelings import get_feelings_by_user
import matplotlib.pyplot as plt
from io import BytesIO

def register_analytics_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_graph_command, commands=["graph"])

async def handle_graph_command(message: types.Message):
    user_id = message.from_user.id
    data = get_feelings_by_user(user_id)

    if not data:
        await message.answer("Нет данных о самочувствии для построения графика.")
        return

    dates = [d["log_date"] for d in data]
    energy = [d["energy"] for d in data]
    mood = [d["mood"] for d in data]
    stress = [d["stress"] for d in data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, energy, label="Энергия", marker='o')
    plt.plot(dates, mood, label="Настроение", marker='o')
    plt.plot(dates, stress, label="Стресс", marker='o')
    plt.title("Твое самочувствие по дням")
    plt.xlabel("Дата")
    plt.ylabel("Оценка (0-10)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    await message.answer_photo(buf, caption="Вот твой график самочувствия 📊")
