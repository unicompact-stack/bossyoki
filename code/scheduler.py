"""Фоновые задачи: напоминания, отчёты, синхронизация."""

import time
import logging
from datetime import datetime, timedelta

log = logging.getLogger('bossyoki')


class Scheduler:
    def __init__(self, db, vk_bot, sync, config):
        self.db = db
        self.vk = vk_bot
        self.sync = sync
        self.config = config
        self.user_id = config['vk_user_id']
        self._report_sent = {}

    def check_reminders(self):
        """Проверяет напоминания каждую минуту."""
        while True:
            try:
                pending = self.db.get_pending_reminders()
                if pending:
                    log.info(f'Найдено {len(pending)} напоминаний')
                for r in pending:
                    log.info(f'Отправляю напоминание: {r["title"]} для {r["user_id"]}')
                    self.vk.send_message(r['user_id'], f'⏰ Напоминание: {r["title"]}')
                    self.db.mark_reminder_sent(r['id'])
                    log.info(f'Напоминание отправлено: {r["title"]}')
            except Exception as e:
                log.error(f'Reminder check error: {e}')
            time.sleep(60)

    def periodic_sync(self):
        """Синхронизация с GitHub каждые 5 минут."""
        while True:
            try:
                self.sync.sync_to_github(force=True)
            except Exception as e:
                log.error(f'Periodic sync error: {e}')
            time.sleep(300)

    def check_daily_report(self):
        """Отправляет отчёт утром (9:00) и вечером (21:00)."""
        while True:
            try:
                now = datetime.now()
                today = now.strftime('%Y-%m-%d')
                hour = now.hour
                minute = now.minute

                morning_key = f'{today}_morning'
                if hour == 9 and minute < 3 and morning_key not in self._report_sent:
                    self._report_sent[morning_key] = True
                    self._send_morning_report()

                evening_key = f'{today}_evening'
                if hour == 21 and minute < 3 and evening_key not in self._report_sent:
                    self._report_sent[evening_key] = True
                    self._send_evening_report()

            except Exception as e:
                log.error(f'Daily report error: {e}')
            time.sleep(60)

    def _send_morning_report(self):
        stats = self.db.get_stats(self.user_id)
        tasks = self.db.get_tasks(self.user_id)
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_tasks = [t for t in tasks if t.get('deadline') == today_str]
        overdue = [t for t in tasks if t.get('deadline') and t['deadline'] < today_str]

        lines = ['☀️ Доброе утро! План на сегодня:']
        if today_tasks:
            lines.append(f'📋 Дел: {len(today_tasks)}')
            for t in today_tasks:
                time_str = f" в {t['time']}" if t.get('time') else ''
                lines.append(f'  • {t["title"]}{time_str}')
        else:
            lines.append('📋 Задач нет — добавь что-нибудь!')

        if overdue:
            lines.append(f'\n⚠️ Просрочено: {len(overdue)}')
            for t in overdue[:3]:
                lines.append(f'  • {t["title"]} ({t["deadline"]})')

        lines.append(f'\n📊 Всего: {stats["done"]}✅ / {stats["active"]}⏳')
        lines.append('\n💪 Давай, ты сможешь!')

        self.vk.send_message(self.user_id, '\n'.join(lines))
        log.info('Утренний отчёт отправлен')

    def _send_evening_report(self):
        stats = self.db.get_stats(self.user_id)
        today_str = datetime.now().strftime('%Y-%m-%d')
        tasks = self.db.get_tasks(self.user_id)
        today_tasks = [t for t in tasks if t.get('deadline') == today_str]
        done_today = [t for t in today_tasks if t['status'] == 'done']
        pending_today = [t for t in today_tasks if t['status'] == 'active']

        lines = ['🌙 Итоги дня:']
        if done_today:
            lines.append(f'✅ Выполнено: {len(done_today)}')
            for t in done_today:
                lines.append(f'  • {t["title"]}')
        else:
            lines.append('✅ Сегодня ничего не выполнено')

        if pending_today:
            lines.append(f'\n⏳ Осталось: {len(pending_today)}')
            for t in pending_today[:3]:
                time_str = f" в {t['time']}" if t.get('time') else ''
                lines.append(f'  • {t["title"]}{time_str}')

        lines.append(f'\n📊 Всего: {stats["done"]}✅ / {stats["active"]}⏳')

        if len(done_today) >= 3:
            lines.append('\n🔥 Ты молодец, отличный день!')
        elif len(done_today) > 0:
            lines.append('\n👍 Неплохо, завтра ещё больше!')
        else:
            lines.append('\n💪 Завтра обязательно получится!')

        self.vk.send_message(self.user_id, '\n'.join(lines))
        log.info('Вечерний отчёт отправлен')
