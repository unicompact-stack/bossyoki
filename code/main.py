#!/usr/bin/env python3
"""BossYoki — проактивный тайм-менеджер."""

import vk_handler
from config import load_config
from timer import start_scheduler

def main():
    config = load_config()
    start_scheduler()
    vk_handler.start(config)

if __name__ == "__main__":
    main()