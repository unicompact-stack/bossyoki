"""Обработчик команд напоминаний."""

import re
from datetime import datetime, timedelta


def parse_reminder_time(text):
    """Парсит время напоминания из текста."""
    t = text.lower().strip()

    # "через 30 минут позвонить"
    match = re.match(r'(?:напомни )?через (\d+) (минут[уыа]?|секунд[уыа]?|час[аов]*) (.+)', t)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        task_text = match.group(3)
        if 'секунд' in unit:
            remind_at = datetime.now() + timedelta(seconds=amount)
        elif 'час' in unit:
            remind_at = datetime.now() + timedelta(hours=amount)
        else:
            remind_at = datetime.now() + timedelta(minutes=amount)
        return remind_at, task_text

    # "завтра 10:00 задача"
    match = re.match(r'(?:напомни )?завтра (\d{1,2}[:\.]?\d{0,2}) (.+)', t)
    if match:
        time_str = match.group(1).replace('.', ':')
        task_text = match.group(2)
        if ':' not in time_str:
            time_str += ':00'
        h, m = map(int, time_str.split(':'))
        remind_at = datetime.now().replace(hour=h, minute=m, second=0) + timedelta(days=1)
        return remind_at, task_text

    # "сегодня 15:00 задача"
    match = re.match(r'(?:напомни )?сегодня (\d{1,2}[:\.]?\d{0,2}) (.+)', t)
    if match:
        time_str = match.group(1).replace('.', ':')
        task_text = match.group(2)
        if ':' not in time_str:
            time_str += ':00'
        h, m = map(int, time_str.split(':'))
        remind_at = datetime.now().replace(hour=h, minute=m, second=0)
        if remind_at < datetime.now():
            remind_at += timedelta(days=1)
        return remind_at, task_text

    # "в 15:00 задача"
    match = re.match(r'(?:напомни )?в (\d{1,2})[:\.]?(\d{0,2}) (.+)', t)
    if match:
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        task_text = match.group(3)
        remind_at = datetime.now().replace(hour=h, minute=m, second=0)
        if remind_at < datetime.now():
            remind_at += timedelta(days=1)
        return remind_at, task_text

    return None, None


def handle_reminder(text, user_id, db):
    """Обрабатывает команды напоминаний."""
    t = text.lower().strip()

    # Создать напоминание
    if t.startswith('напомни ') or re.match(r'через \d+ (минут|секунд|час)', t):
        remind_at, task_text = parse_reminder_time(t)
        if remind_at and task_text:
            clean = re.sub(r'^напомни\s+(мне\s+)?', '', task_text, flags=re.IGNORECASE).strip()
            if not clean:
                clean = task_text
            time_str = remind_at.strftime('%H:%M')
            task_id = db.add_task(user_id, clean, remind_at.strftime('%Y-%m-%d'), 'medium', time=time_str)
            db.add_reminder(task_id, remind_at.strftime('%Y-%m-%d %H:%M:%S'))
            return f'⏰ Напоминание в {time_str}: {clean}'
        return 'Не понял время.\nПример: напомни через 30 минут позвонить'

    # Список напоминаний
    if t in ['напоминания', 'активные напоминания']:
        reminders = db.get_active_reminders(user_id)
        if not reminders:
            return 'Активных напоминаний нет.'
        lines = ['⏰ Напоминания:\n']
        for i, r in enumerate(reminders, 1):
            lines.append(f"{i}. {r['remind_at'][:16]} — {r['title']}")
        return '\n'.join(lines)

    return None
