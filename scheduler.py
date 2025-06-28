from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from models import get_reminder_time

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.start()

def schedule_user_reminder(user_id: int, bot: Bot):
    job_id = f"reminder_{user_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass  # Если задачи не было, игнорируем ошибку

    time_str = get_reminder_time(user_id)
    if not time_str:
        return  # если нет времени — не планируем

    hour, minute = map(int, time_str.split(':'))

    scheduler.add_job(
        send_reminder,
        "cron",
        hour=hour,
        minute=minute,
        args=[user_id, bot],
        id=job_id,
        replace_existing=True
    )

async def send_reminder(user_id: int, bot: Bot):
    try:
        await bot.send_message(user_id, "⏰ Напоминание: не забудь отметить привычки и ощущения сегодня!")
    except Exception as e:
        print(f"Не удалось отправить напоминание для {user_id}: {e}")
