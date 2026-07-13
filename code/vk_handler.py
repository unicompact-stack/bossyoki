"""Интеграция с VK API."""

import requests
from config import load_config
from tools import add_task, load_tasks

def start(config: dict):
    """Запуск обработчика VK."""
    print("BossYoki запущен и ждёт сообщений в VK...")
    # Здесь будет longpoll или webhook
    # Пока просто имитация
    while True:
        message = input("Сообщение от пользователя: ")
        if message.startswith("добавь задачу"):
            text = message.replace("добавь задачу", "").strip()
            task = add_task(text, "сегодня")
            print(f"Задача добавлена: {task['text']}")
        elif message == "покажи задачи":
            tasks = load_tasks()
            for t in tasks:
                print(f"{t['id']}. {t['text']} ({t['status']})")