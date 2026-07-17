"""Настройка логирования."""

import os
import logging


def setup_logging(log_dir=None):
    if log_dir is None:
        log_dir = os.path.dirname(__file__)

    log_file = os.path.join(log_dir, 'bossyoki.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('bossyoki')
