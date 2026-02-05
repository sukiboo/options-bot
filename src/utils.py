from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone


def setup_logger(log_dir: str = "logs", level: int = logging.DEBUG) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m')}.log")

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()

    class UtcFormatter(logging.Formatter):
        converter = time.gmtime

    formatter = UtcFormatter(
        fmt="%(asctime)sZ | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    for lib in ["telegram", "telegram.bot", "telegram.ext"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger
