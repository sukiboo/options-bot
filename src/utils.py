from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))


def setup_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"

    logger = logging.getLogger("notify_bot")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # avoid duplicate handlers on reloads

    # Make logging timestamps UTC
    class UtcFormatter(logging.Formatter):
        converter = time.gmtime

    formatter = UtcFormatter(
        fmt="%(asctime)sZ | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)

    # Stdout handler
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
