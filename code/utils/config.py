"""Конфигурация бота из .env файла."""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))


def load_config():
    return {
        'vk_token': os.getenv('VK_TOKEN_MESSAGES'),
        'group_id': int(os.getenv('VK_GROUP_ID', '73303964')),
        'github_token': os.getenv('GITHUB_TOKEN', os.getenv('GROQ_API_KEY')),
        'vk_user_id': int(os.getenv('VK_USER_ID', '114439622')),
        'github_repo': 'unicompact-stack/bossyoki',
        'github_file': 'tasks.json',
        'port': int(os.getenv('PORT', '10000')),
    }
