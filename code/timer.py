"""Планировщик напоминаний."""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import vk_api
from vk_api.utils import get_random_id
from config import load_config
from tools import load_tasks

scheduler = BackgroundScheduler()
vk_api_instance = None
user_id = None


def init_vk(vk_api_obj, uid: int):
    """Инициализировать VK API для напоминаний."""
    global vk_api_instance, user_id
    vk_api_instance = vk_api_obj
    user_id = uid


def schedule_reminder(task_id: int, time: str):
    """Запланировать напоминание."""
    hour, minute = map(int, time.split(":"))
    scheduler.add_job(
        send_reminder,
        "cron",
        hour=hour,
        minute=minute,
        args=[task_id],
        id=f"reminder_{task_id}_{time}",
        replace_existing=True
    )


def send_reminder(task_id: int):
    """Отправить напоминание пользователю."""
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return

    message = f"⏰ Напоминание: {task['text']}"

    if vk_api_instance and user_id:
        try:
            vk_api_instance.messages.send(
                user_id=user_id,
                message=message,
                random_id=get_random_id()
            )
        except Exception as e:
            print(f"Ошибка отправки напоминания: {e}")


def check_overdue_reminders():
    """Проверить просроченные задачи и напомнить."""
    tasks = load_tasks()
    today = datetime.now().strftime("%Y-%m-%d")
    for task in tasks:
        if task["status"] == "active" and task.get("deadline"):
            if task["deadline"] < today:
                if vk_api_instance and user_id:
                    message = f"⚠️ Просрочено: {task['text']}"
                    try:
                        vk_api_instance.messages.send(
                            user_id=user_id,
                            message=message,
                            random_id=get_random_id()
                        )
                    except Exception:
                        pass


def start_scheduler():
    """Запустить планировщик."""
    scheduler.add_job(
        check_overdue_reminders,
        "cron",
        hour=9,
        minute=0,
        id="overdue_check"
    )
    scheduler.start()
