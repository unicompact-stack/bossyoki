"""Определение таблиц SQLite."""

import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks.db')


def init_db():
    """Создаёт таблицы если их нет."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute('PRAGMA foreign_keys = ON')

    conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        note TEXT DEFAULT '',
        deadline TEXT,
        time TEXT DEFAULT '',
        priority TEXT DEFAULT 'medium',
        category TEXT DEFAULT '',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        remind_at TIMESTAMP NOT NULL,
        sent INTEGER DEFAULT 0,
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.execute("DELETE FROM conversations WHERE created_at < datetime('now', '-30 days')")
    conn.commit()
    conn.close()
