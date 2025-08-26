from __future__ import annotations

import os
from datetime import datetime, timezone

import telegram

from src.constants import BOT_NAME
from src.utils import setup_logger

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

logger = setup_logger()


class OptionsBot:
    def __init__(self) -> None:
        logger.info(f"{BOT_NAME} initializing...")
        self.setup_telegram_bot()

    def setup_telegram_bot(self) -> None:
        if not TELEGRAM_BOT_TOKEN:
            msg = "TELEGRAM_BOT_TOKEN is not set!"
            logger.error(msg)
            raise SystemExit(msg)
        if not TELEGRAM_CHAT_ID:
            msg = "TELEGRAM_CHAT_ID is not set!"
            logger.error(msg)
            raise SystemExit(msg)

        self.telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self.send_telegram_message(
            msg=f"{BOT_NAME} started at {datetime.now(timezone.utc).isoformat()}"
        )

    def send_telegram_message(self, msg: str) -> None:
        try:
            self.telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
            logger.info("[telegram] sent: %s", msg)
        except Exception as e:
            logger.error("[telegram] error: %s", e)


if __name__ == "__main__":
    bot = OptionsBot()
