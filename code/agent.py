"""AI-агент на GitHub Models."""

import requests
from config import load_config
from prompts import SYSTEM_PROMPT

def ask_ai(prompt: str) -> str:
    """Отправить запрос к AI и получить ответ."""
    config = load_config()
    headers = {
        "Authorization": f"Bearer {config['github_token']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config["ai_model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    response = requests.post(
        config["ai_api_url"],
        headers=headers,
        json=data
    )
    return response.json()["choices"][0]["message"]["content"]