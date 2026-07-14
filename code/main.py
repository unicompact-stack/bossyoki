#!/usr/bin/env python3
"""BossYoki — проактивный тайм-менеджер.
Только напоминания через VK. Без диалога.
"""

import vk_api
from vk_api.utils import get_random_id
from apscheduler.schedulers.background import BackgroundScheduler
from config import load_config
from tools import load_tasks
from datetime import datetime

scheduler = BackgroundScheduler()
vk = None
user_id = None


def send_message(text: str):
    """Отправить сообщение в VK."""
    if vk and user_id:
        try:
            vk.messages.send(
                user_id=user_id,
                message=text,
                random_id=get_random_id()
            )
            print(f"[VK] {text}")
        except Exception as e:
            print(f"[VK Error] {e}")


def check_reminders():
    """Проверить задачи и отправить напоминания."""
    tasks = load_tasks()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_hour = now.hour

    for task in tasks:
        if task["status"] != "active":
            continue

        deadline = task.get("deadline", "")

        # Просроченные
        if deadline and deadline < today:
            send_message(f"⚠️ Просрочено: {task['text']}")
            continue

        # На сегодня утром (9:00)
        if deadline == today and current_hour == 9:
            send_message(f"📋 Сегодня: {task['text']}")


def main():
    global vk, user_id

    config = load_config()
    user_id = int(config["vk_user_id"])

    vk_session = vk_api.VkApi(token=config["vk_token"])
    vk = vk_session.get_api()

    # Проверка каждые 30 минут
    scheduler.add_job(check_reminders, "interval", minutes=30, id="reminders")
    # Утренняя проверка в 9:00
    scheduler.add_job(check_reminders, "cron", hour=9, minute=0, id="morning")
    # Вечерняя проверка в 18:00
    scheduler.add_job(check_reminders, "cron", hour=18, minute=0, id="evening")
    scheduler.start()

    print(f"BossYoki запущен. Напоминания для user_id={user_id}")
    print("Ctrl+C для остановки")

    # Держим процесс живым
    try:
        while True:
            pass
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("Остановлен")


if __name__ == "__main__":
    main()
