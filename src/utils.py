from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

import pytz  # type: ignore


def setup_logger(log_dir: str = "logs", level: int = logging.DEBUG) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m')}.log")

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()  # avoid duplicate handlers on reloads

    # Make logging timestamps UTC
    class UtcFormatter(logging.Formatter):
        converter = time.gmtime

    formatter = UtcFormatter(
        fmt="%(asctime)sZ | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)

    # Stdout handler
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    # Silence third-party library debug logs
    for lib in ["telegram", "telegram.bot", "telegram.ext"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger


def get_timezone() -> pytz.BaseTzInfo:
    """Parse and validate timezone from environment variable."""
    timezone_env = os.getenv("TZ", "America/New_York")
    try:
        return pytz.timezone(timezone_env)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone("America/New_York")


def parse_run_times(env_var: str) -> list[str]:
    """Parse and validate `env_var` from environment variable."""
    run_times = [t.strip() for t in os.getenv(env_var, "").split(",") if t.strip()]

    if not run_times:
        raise ValueError(
            f"No {env_var} specified, set {env_var} environment variable (e.g., '09:30,15:30')"
        )

    for time_str in run_times:
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise ValueError(
                f"Invalid time format: {time_str}. Expected format: HH:MM (e.g., '09:30')"
            )

    return run_times
