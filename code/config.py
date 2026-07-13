"""Загрузка конфигурации из .env."""

import os
from pathlib import Path

def load_config() -> dict:
    """Загрузить переменные окружения из .env файла."""
    env_path = Path(__file__).parent.parent / ".env"
    config = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    # Также из переменных окружения
    config["vk_token"] = os.getenv("VK_TOKEN", config.get("VK_TOKEN", ""))
    config["github_token"] = os.getenv("GITHUB_TOKEN", config.get("GITHUB_TOKEN", ""))
    # GitHub Models API
    config["ai_api_url"] = "https://models.inference.ai.azure.com/chat/completions"
    config["ai_model"] = "gpt-4o-mini"
    return config