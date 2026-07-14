"""Интеграция с VK API через longpoll."""

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from config import load_config
from tools import add_task, load_tasks, complete_task, delete_task
from agent import ask_ai


def start(config: dict):
    """Запуск обработчика VK."""
    vk_session = vk_api.VkApi(token=config["vk_token"])
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    print("BossYoki запущен и ждёт сообщений в VK...")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text.lower().strip()

            # Команды
            if text.startswith("добавь ") or text.startswith("сделай "):
                task_text = event.text.split(" ", 1)[1] if " " in event.text else ""
                if task_text:
                    task = add_task(task_text, "сегодня")
                    reply = f"Добавил: {task['text']}"
                else:
                    reply = "Укажи текст задачи"

            elif text in ("задачи", "список", "что делаю"):
                tasks = load_tasks()
                active = [t for t in tasks if t["status"] == "active"]
                if active:
                    lines = [f"{t['id']}. {t['text']}" for t in active[:10]]
                    reply = "Твои задачи:\n" + "\n".join(lines)
                else:
                    reply = "Нет активных задач"

            elif text.startswith("выполни ") or text.startswith("готово "):
                try:
                    task_id = int(text.split()[-1])
                    if complete_task(task_id):
                        reply = f"Задача #{task_id} выполнена!"
                    else:
                        reply = "Задача не найдена"
                except ValueError:
                    reply = "Укажи номер задачи"

            elif text.startswith("удали ") or text.startswith("убери "):
                try:
                    task_id = int(text.split()[-1])
                    if delete_task(task_id):
                        reply = f"Задача #{task_id} удалена"
                    else:
                        reply = "Задача не найдена"
                except ValueError:
                    reply = "Укажи номер задачи"

            else:
                # Отправляем в AI
                tasks = load_tasks()
                context = "\n".join([f"- {t['text']} ({t['status']})" for t in tasks[-10:]])
                prompt = f"Текущие задачи:\n{context}\n\nСообщение: {event.text}"
                try:
                    reply = ask_ai(prompt)
                except Exception as e:
                    reply = f"Ошибка AI: {str(e)[:50]}"

            vk.messages.send(
                user_id=user_id,
                message=reply,
                random_id=get_random_id()
            )
