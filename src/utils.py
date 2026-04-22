from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Callable

from apscheduler.schedulers.base import STATE_STOPPED
from apscheduler.schedulers.blocking import BlockingScheduler

MAX_SCHEDULER_WAIT = 3600


class SafeBlockingScheduler(BlockingScheduler):
    def _main_loop(self) -> None:  # type: ignore[override]
        wait_seconds = MAX_SCHEDULER_WAIT
        while self.state != STATE_STOPPED:  # type: ignore[attr-defined]
            self._event.wait(wait_seconds)  # type: ignore[attr-defined]
            self._event.clear()  # type: ignore[attr-defined]
            wait_seconds = min(self._process_jobs() or MAX_SCHEDULER_WAIT, MAX_SCHEDULER_WAIT)


class cached_property_ttl:
    """A property descriptor with time-based caching. Usage: @cached_property_ttl(ttl=60)."""

    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.func: Callable[..., Any] = lambda _: None

    def __call__(self, func: Callable[..., Any]) -> cached_property_ttl:
        self.func = func
        return self

    def __set_name__(self, owner: type, name: str) -> None:
        self.attr = f"_ttl_{name}"

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        cached = getattr(obj, self.attr, None)
        if cached is not None and time.time() - cached[1] < self.ttl:
            return cached[0]
        result = self.func(obj)
        setattr(obj, self.attr, (result, time.time()))
        return result


class _MonthlyRotatingHandler(TimedRotatingFileHandler):
    def __init__(self, log_dir: str, **kwargs: Any) -> None:
        self.log_dir = log_dir
        super().__init__(self._current_log_path(), when="MIDNIGHT", **kwargs)

    def _current_log_path(self) -> str:
        return os.path.join(self.log_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m')}.log")

    def shouldRollover(self, record: logging.LogRecord) -> int:
        return 1 if self._current_log_path() != self.baseFilename else 0

    def doRollover(self) -> None:
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore[assignment]
        self.baseFilename = self._current_log_path()
        self.stream = self._open()


def setup_logger(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()

    class UtcFormatter(logging.Formatter):
        converter = time.gmtime  # type: ignore[assignment]

    formatter = UtcFormatter(
        fmt="%(asctime)sZ | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    fh = _MonthlyRotatingHandler(log_dir, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    for lib in ["telegram", "telegram.bot", "telegram.ext", "httpx", "httpcore"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger
