"""Планировщик напоминаний."""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

scheduler = BackgroundScheduler()

def schedule_reminder(task_id: int, time: str):
    """Запланировать напоминание."""
    hour, minute = map(int, time.split(":"))
    scheduler.add_job(
        send_reminder,
        "cron",
        hour=hour,
        minute=minute,
        args=[task_id],
        id=f"reminder_{task_id}_{time}"
    )

def send_reminder(task_id: int):
    """Отправить напоминание (заглушка)."""
    print(f"Напоминание для задачи {task_id}")

def start_scheduler():
    """Запустить планировщик."""
    scheduler.start()