from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from telegram import Bot

from src.utils import setup_logger

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_startup_ping(bot: Bot, logger: logging.Logger) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    msg = f"options-bot started at {ts}"
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        logger.info("[telegram] sent: %s", msg)
    except Exception as e:
        logger.error("[telegram] error: %s", e)


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set!")
    if not TELEGRAM_CHAT_ID:
        raise SystemExit("TELEGRAM_CHAT_ID is not set!")

    logger = setup_logger()
    logger.info("options-bot initializing")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    send_startup_ping(bot, logger)


if __name__ == "__main__":
    main()
