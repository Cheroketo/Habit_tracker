from aiogram import Dispatcher, types

def register_general_handlers(dp: Dispatcher):
    @dp.message_handler(commands=["start", "help"])
    async def send_welcome(msg: types.Message):
        await msg.answer("""
Привет! Я твой трекер привычек 💪
Вот что я умею:

/addhabit — добавить новую привычку
/list — список всех твоих привычек
/done — отметить привычку выполненной
/today — что ты сегодня сделал
/feelings — записать своё состояние
/graph — график твоих ощущений
/remindme — установить напоминание
/stopreminder — отключить напоминание
/habitstats — статистика по привычке
/menu — кнопочное меню для всех команд
        """)