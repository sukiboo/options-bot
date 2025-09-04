from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

import pytz  # type: ignore

logger = logging.getLogger()


def setup_logger(log_dir: str = "logs") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m')}.log")

    logger = logging.getLogger()
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


def parse_run_times() -> list[str]:
    """Parse and validate RUN_TIMES from environment variable."""
    run_times = [t.strip() for t in os.getenv("RUN_TIMES", "").split(",") if t.strip()]

    if not run_times:
        raise ValueError(
            "No RUN_TIMES specified, set RUN_TIMES environment variable (e.g., '09:30,15:30')"
        )

    for time_str in run_times:
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise ValueError(
                f"Invalid time format: {time_str}. Expected format: HH:MM (e.g., '09:30')"
            )

    return run_times


def get_timezone() -> pytz.BaseTzInfo:
    """Parse and validate timezone from environment variable."""
    timezone_env = os.getenv("TZ", "America/New_York")
    try:
        return pytz.timezone(timezone_env)
    except pytz.UnknownTimeZoneError:
        logger.warning(f"Unknown timezone '{timezone_env}'. Using 'America/New_York' as fallback.")
        return pytz.timezone("America/New_York")
