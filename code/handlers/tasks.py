"""Обработчик команд задач."""

import re
from datetime import datetime, timedelta


def handle_tasks(text, user_id, db):
    """Обрабатывает команды задач: добавить, список, выполнено, удалить, отчёт."""
    t = text.lower().strip()

    # Список задач
    if t in ['задачи', 'список задач', 'мои задачи', '!список', 'список']:
        tasks = db.get_tasks(user_id)
        if not tasks:
            return '📋 Задач пока нет.\nНапиши "добавить [текст]" чтобы создать.'
        pri_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
        lines = ['📋 Твои задачи:\n']
        for task in tasks:
            pri = pri_icons.get(task['priority'], '🟡')
            deadline = f" ({task['deadline']})" if task.get('deadline') else ''
            lines.append(f"#{task['id']} {pri} {task['title']}{deadline}")
        return '\n'.join(lines)

    # Добавить задачу
    if t.startswith('добавить ') or t.startswith('новая ') or t.startswith('добавь '):
        task_text = text.split(' ', 1)[1] if ' ' in text else ''
        if not task_text:
            return 'Укажи текст задачи.\nПример: добавить отчёт по рекламе'

        lower = task_text.lower()
        deadline = None
        priority = 'medium'

        if 'срочно' in lower or 'важно' in lower or 'горит' in lower:
            priority = 'high'
        elif 'потом' in lower or 'не срочно' in lower:
            priority = 'low'

        if 'сегодня' in lower:
            deadline = datetime.now().strftime('%Y-%m-%d')
        elif 'завтра' in lower:
            deadline = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        clean_title = re.sub(
            r'сегодня|завтра|срочно|важно|горит|потом|не срочно',
            '', task_text, flags=re.IGNORECASE
        ).strip()
        if not clean_title:
            clean_title = task_text

        task_id = db.add_task(user_id, clean_title, deadline, priority)
        pri_label = '🔴 Срочно' if priority == 'high' else '🟢 Потом' if priority == 'low' else '🟡 Важно'
        date_label = f" 📅 {deadline}" if deadline else ''
        return f'✅ Задача #{task_id}: {clean_title}\n{pri_label}{date_label}'

    # Выполнено
    if t.startswith('выполнено ') or t.startswith('сделано ') or t.startswith('выполни '):
        try:
            task_id = int(t.split()[1])
            if db.complete_task(user_id, task_id):
                return f'✅ Задача #{task_id} выполнена! Молодец!'
            return f'Задача #{task_id} не найдена.'
        except (ValueError, IndexError):
            return 'Укажи номер задачи.\nПример: выполнено 1'

    # Удалить
    if t.startswith('удалить ') or t.startswith('убрать ') or t.startswith('!удалить '):
        try:
            task_id = int(t.split()[-1])
            if db.delete_task(user_id, task_id):
                return f'🗑 Задача #{task_id} удалена.'
            return f'Задача #{task_id} не найдена.'
        except (ValueError, IndexError):
            return 'Укажи номер задачи.'

    # Отчёт
    if t == '!отчёт' or t == '!отчет' or t == 'отчёт':
        stats = db.get_stats(user_id)
        return (
            f'📊 Отчёт:\n'
            f'✅ Выполнено: {stats["done"]}\n'
            f'📋 Активных: {stats["active"]}\n'
            f'📌 Сегодня: {stats["today"]}\n'
            f'⚠️ Просрочено: {stats["overdue"]}\n'
            f'📁 Всего: {stats["total"]}'
        )

    return None
