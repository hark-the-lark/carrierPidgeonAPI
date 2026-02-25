# bookService/service/app/logging.py

import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        force=True,  # ensures reload works correctly
    )