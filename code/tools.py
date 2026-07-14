"""Инструменты для работы с задачами."""

import json
from pathlib import Path
from datetime import datetime

TASKS_FILE = Path("tasks.json")

def load_tasks() -> list:
    """Загрузить задачи из файла."""
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []

def save_tasks(tasks: list):
    """Сохранить задачи в файл."""
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))

def add_task(text: str, deadline: str) -> dict:
    """Добавить новую задачу."""
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "text": text,
        "deadline": deadline,
        "status": "active",
        "created": datetime.now().isoformat(),
        "reminders": []
    }
    tasks.append(task)
    save_tasks(tasks)
    return task

def complete_task(task_id: int) -> bool:
    """Отметить задачу как выполненную."""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "completed"
            save_tasks(tasks)
            return True
    return False


def delete_task(task_id: int) -> bool:
    """Удалить задачу."""
    tasks = load_tasks()
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            save_tasks(tasks)
            return True
    return False