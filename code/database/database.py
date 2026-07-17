"""Операции с базой данных SQLite."""

import sqlite3
import os
from datetime import datetime

from .models import DB_FILE


class Database:
    def __init__(self):
        self.db_path = DB_FILE

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    # === Tasks ===

    def add_task(self, user_id, title, deadline=None, priority='medium',
                 category='', note='', time=None):
        conn = self._connect()
        try:
            cur = conn.execute(
                'INSERT INTO tasks (user_id, title, note, deadline, priority, category, time) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (user_id, title, note, deadline, priority, category, time)
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_tasks(self, user_id, status='active'):
        conn = self._connect()
        try:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY '
                "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, deadline",
                (user_id, status)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_task(self, task_id, user_id):
        conn = self._connect()
        try:
            row = conn.execute(
                'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
                (task_id, user_id)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def complete_task(self, user_id, task_id):
        conn = self._connect()
        try:
            now = datetime.now().isoformat()
            cur = conn.execute(
                'UPDATE tasks SET status = ?, completed_at = ? WHERE id = ? AND user_id = ?',
                ('done', now, task_id, user_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def delete_task(self, user_id, task_id):
        conn = self._connect()
        try:
            cur = conn.execute(
                'DELETE FROM tasks WHERE id = ? AND user_id = ?',
                (task_id, user_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def get_stats(self, user_id):
        conn = self._connect()
        try:
            total = conn.execute(
                'SELECT COUNT(*) FROM tasks WHERE user_id = ?', (user_id,)
            ).fetchone()[0]
            done = conn.execute(
                'SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?',
                (user_id, 'done')
            ).fetchone()[0]
            active = conn.execute(
                'SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?',
                (user_id, 'active')
            ).fetchone()[0]
            overdue = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'active' AND deadline < date('now')",
                (user_id,)
            ).fetchone()[0]
            today_count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'active' AND deadline = date('now')",
                (user_id,)
            ).fetchone()[0]
            return {
                'total': total, 'done': done, 'active': active,
                'overdue': overdue, 'today': today_count
            }
        finally:
            conn.close()

    def get_all_tasks_for_sync(self, user_id):
        conn = self._connect()
        try:
            rows = conn.execute(
                'SELECT * FROM tasks WHERE user_id = ? ORDER BY id', (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # === Reminders ===

    def add_reminder(self, task_id, remind_at):
        conn = self._connect()
        try:
            conn.execute(
                'INSERT INTO reminders (task_id, remind_at) VALUES (?, ?)',
                (task_id, remind_at)
            )
            conn.commit()
        finally:
            conn.close()

    def get_pending_reminders(self):
        conn = self._connect()
        try:
            now = datetime.now().isoformat()
            rows = conn.execute(
                'SELECT r.id, r.task_id, r.remind_at, t.title, t.user_id '
                'FROM reminders r JOIN tasks t ON r.task_id = t.id '
                'WHERE r.sent = 0 AND r.remind_at <= ?',
                (now,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_reminder_sent(self, reminder_id):
        conn = self._connect()
        try:
            conn.execute(
                'UPDATE reminders SET sent = 1 WHERE id = ?', (reminder_id,)
            )
            conn.commit()
        finally:
            conn.close()

    def get_active_reminders(self, user_id):
        conn = self._connect()
        try:
            rows = conn.execute(
                'SELECT r.remind_at, t.title FROM reminders r '
                'JOIN tasks t ON r.task_id = t.id '
                'WHERE t.user_id = ? AND r.sent = 0 ORDER BY r.remind_at',
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # === Conversations ===

    def save_message(self, user_id, role, message):
        conn = self._connect()
        try:
            conn.execute(
                'INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)',
                (user_id, role, message)
            )
            conn.commit()
        finally:
            conn.close()

    def get_conversation_history(self, user_id, limit=20):
        conn = self._connect()
        try:
            rows = conn.execute(
                'SELECT role, message FROM conversations WHERE user_id = ? '
                'ORDER BY id DESC LIMIT ?',
                (user_id, limit)
            ).fetchall()
            return [{'role': r['role'], 'content': r['message']} for r in reversed(rows)]
        finally:
            conn.close()

    def clear_conversation(self, user_id):
        conn = self._connect()
        try:
            conn.execute(
                'DELETE FROM conversations WHERE user_id = ?', (user_id,)
            )
            conn.commit()
        finally:
            conn.close()

    # === Dashboard API ===

    def get_api_data(self, user_id):
        conn = self._connect()
        try:
            msgs = []
            for r in conn.execute(
                "SELECT role, message, created_at FROM conversations ORDER BY id DESC LIMIT 30"
            ).fetchall():
                row = dict(r)
                t = row.get('created_at', '')
                try:
                    from datetime import timedelta
                    utc = datetime.strptime(t[:19], '%Y-%m-%d %H:%M:%S')
                    local = utc + timedelta(hours=3)
                    row['time'] = local.strftime('%H:%M')
                    row['date'] = local.strftime('%d.%m')
                except Exception:
                    row['time'] = t[11:16] if len(t) > 16 else t[:5]
                    row['date'] = t[:10]
                msgs.append(row)
            msgs.reverse()

            tasks = [dict(r) for r in conn.execute(
                "SELECT id, title, priority, deadline, time, status "
                "FROM tasks WHERE user_id = ? ORDER BY id DESC LIMIT 50",
                (user_id,)
            ).fetchall()]

            stats = {
                'active': conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'active'",
                    (user_id,)
                ).fetchone()[0],
                'done': conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'done'",
                    (user_id,)
                ).fetchone()[0],
                'today': conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'active' AND deadline = date('now')",
                    (user_id,)
                ).fetchone()[0],
                'overdue': conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'active' AND deadline < date('now')",
                    (user_id,)
                ).fetchone()[0],
            }
            return {'messages': msgs, 'tasks': tasks, 'stats': stats}
        finally:
            conn.close()
