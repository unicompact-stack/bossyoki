"""Синхронизация задач с GitHub."""

import json
import time
import base64
import logging
import requests
from datetime import datetime

log = logging.getLogger('bossyoki')


class GitHubSync:
    def __init__(self, config, db):
        self.token = config['github_token']
        self.repo = config['github_repo']
        self.file = config['github_file']
        self.db = db
        self.user_id = config['vk_user_id']
        self._last_sync = 0
        self._interval = 30

    def _get_headers(self):
        return {'Authorization': f'token {self.token}'}

    def _get_sha(self):
        try:
            r = requests.get(
                f'https://api.github.com/repos/{self.repo}/contents/{self.file}',
                headers=self._get_headers(),
                timeout=10
            )
            if r.status_code == 200:
                return r.json().get('sha', '')
        except Exception:
            pass
        return ''

    def sync_to_github(self, force=False):
        """Бот пишет в GitHub tasks.json — главный источник."""
        now = time.time()
        if not force and (now - self._last_sync) < self._interval:
            return
        self._last_sync = now

        if not self.token or not self.token.startswith('ghp_'):
            log.warning('GitHub токен не настроен')
            return

        try:
            tasks = self.db.get_all_tasks_for_sync(self.user_id)
            tasks_list = []
            for t in tasks:
                tasks_list.append({
                    'id': str(t['id']),
                    'title': t['title'],
                    'note': t['note'] or '',
                    'date': t['deadline'] or '',
                    'time': t['time'] or '',
                    'priority': t['priority'],
                    'category': t['category'] or '',
                    'done': t['status'] == 'done',
                    'created': t['created_at'] or ''
                })

            data = json.dumps({
                'version': '2.0',
                'source': 'vk_bot',
                'updatedAt': datetime.now().isoformat(),
                'tasks': tasks_list
            }, ensure_ascii=False, indent=2)

            sha = self._get_sha()
            body = {
                'message': f'🔄 Бот обновил задачи ({datetime.now().strftime("%H:%M")})',
                'content': base64.b64encode(data.encode()).decode(),
            }
            if sha:
                body['sha'] = sha

            r = requests.put(
                f'https://api.github.com/repos/{self.repo}/contents/{self.file}',
                headers={**self._get_headers(), 'Content-Type': 'application/json'},
                json=body,
                timeout=10
            )
            if r.status_code in (200, 201):
                log.info(f'GitHub sync OK: {len(tasks_list)} задач')
            else:
                log.error(f'GitHub sync failed: {r.status_code} — {r.text[:200]}')
        except Exception as e:
            log.error(f'GitHub sync error: {e}')

    def load_from_github(self):
        """Загружает задачи из GitHub tasks.json."""
        try:
            r = requests.get(
                f'https://api.github.com/repos/{self.repo}/contents/{self.file}',
                timeout=10
            )
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode()
                data = json.loads(content)
                tasks = data.get('tasks', [])

                existing = {t['title'].lower() for t in self.db.get_tasks(self.user_id)}

                added = 0
                for t in tasks:
                    if t.get('done'):
                        continue
                    if t['title'].lower() not in existing:
                        self.db.add_task(
                            self.user_id, t['title'],
                            note=t.get('note', ''),
                            deadline=t.get('date', ''),
                            priority=t.get('priority', 'medium'),
                            category=t.get('category', ''),
                            time=t.get('time', '')
                        )
                        added += 1

                if added:
                    log.info(f'Загружено {added} задач с GitHub')
                return added
        except Exception as e:
            log.error(f'GitHub load error: {e}')
        return 0
