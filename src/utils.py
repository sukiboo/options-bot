from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable


class cached_property_ttl:
    """A property descriptor with time-based caching. Usage: @cached_property_ttl(ttl=60)"""

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


def setup_logger(log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m')}.log")

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()

    class UtcFormatter(logging.Formatter):
        converter = time.gmtime  # type: ignore[assignment]

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

    for lib in ["telegram", "telegram.bot", "telegram.ext", "httpx", "httpcore"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logger
