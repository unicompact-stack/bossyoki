"""AI-интеграция через GitHub Models."""

import re
import logging
import requests
from datetime import datetime, timedelta

from utils.prompts import get_tasks_context

log = logging.getLogger('bossyoki')


def handle_ai(text, user_id, db, config):
    """Отправляет запрос в AI и парсит команды из ответа."""
    github_key = config['github_token']
    if not github_key:
        return None

    try:
        tasks = db.get_tasks(user_id)
        stats = db.get_stats(user_id)
        history = db.get_conversation_history(user_id, limit=20)

        system = get_tasks_context(tasks, stats)

        messages = [{'role': 'system', 'content': system}]
        messages.extend(history)

        r = requests.post(
            'https://models.inference.ai.azure.com/chat/completions',
            headers={
                'Authorization': f'Bearer {github_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': messages,
                'max_tokens': 500,
                'temperature': 0.7
            },
            timeout=15
        )
        data = r.json()
        reply = data['choices'][0]['message']['content']

        # Парсим команды AI
        _parse_ai_actions(reply, user_id, db)

        # Убираем команды из ответа
        clean = re.sub(r'\[ADD:\s*.+?\]', '', reply)
        clean = re.sub(r'\[DONE:\s*\d+\]', '', clean)
        clean = re.sub(r'\[DEL:\s*\d+\]', '', clean)
        clean = clean.strip()
        if not clean:
            clean = 'Готово!'
        return clean
    except Exception as e:
        log.error(f'AI error: {e}')
        return None


def _parse_ai_actions(reply, user_id, db):
    """Парсит команды [ADD: ...], [DONE: ...], [DEL: ...] из ответа AI."""
    # ADD
    add_match = re.search(r'\[ADD:\s*(.+?)\]', reply)
    if add_match:
        parts = add_match.group(1).split(',')
        title = parts[0].strip()
        deadline = parts[1].strip() if len(parts) > 1 else None
        priority = parts[2].strip() if len(parts) > 2 else 'medium'
        time_str = parts[3].strip() if len(parts) > 3 else None

        # Если время не в 4м параметре — ищем в заголовке
        if not time_str or not re.match(r'\d{1,2}:\d{2}', time_str):
            full_text = title + ' ' + (deadline or '')
            time_match = re.search(r'в (\d{1,2})[:\.]?(\d{0,2})', full_text.lower())
            if time_match:
                h = int(time_match.group(1))
                m = int(time_match.group(2)) if time_match.group(2) else 0
                if 0 <= h <= 23 and 0 <= m <= 59:
                    time_str = f'{h:02d}:{m:02d}'
        elif not re.match(r'^\d{1,2}:\d{2}$', time_str):
            time_str = None

        # Парсим дату
        if deadline == 'сегодня' or (deadline and 'сегодня' in deadline.lower()):
            deadline = datetime.now().strftime('%Y-%m-%d')
        elif deadline == 'завтра' or (deadline and 'завтра' in deadline.lower()):
            deadline = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        elif deadline and re.match(r'\d{4}-\d{2}-\d{2}', deadline):
            pass
        elif deadline and re.match(r'\d{2}\.\d{2}', deadline):
            day, month = deadline.split('.')
            deadline = f'{datetime.now().year}-{month}-{day}'
        else:
            deadline = datetime.now().strftime('%Y-%m-%d')

        # Убираем время из названия задачи
        clean_title = re.sub(r'в \d{1,2}[:\.]?\d{0,2}\s*(утра|вечера|дня)?', '', title, flags=re.IGNORECASE).strip()
        if not clean_title:
            clean_title = title

        task_id = db.add_task(user_id, clean_title, deadline, priority, time=time_str)

        # Если было время — создаём напоминание
        if time_str and task_id:
            try:
                h, m = map(int, time_str.split(':'))
                remind_dt = datetime.now().replace(hour=h, minute=m, second=0)
                if remind_dt < datetime.now():
                    remind_dt += timedelta(days=1)
                db.add_reminder(task_id, remind_dt.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception:
                pass

    # DONE
    done_match = re.search(r'\[DONE:\s*(\d+)\]', reply)
    if done_match:
        db.complete_task(user_id, int(done_match.group(1)))

    # DEL
    del_match = re.search(r'\[DEL:\s*(\d+)\]', reply)
    if del_match:
        db.delete_task(user_id, int(del_match.group(1)))
