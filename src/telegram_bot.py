from __future__ import annotations

import logging
import os

import telegram

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

logger = logging.getLogger()


class TelegramBot:
    def __init__(self) -> None:
        self.setup()

    def setup(self) -> None:
        if not TELEGRAM_BOT_TOKEN:
            msg = "TELEGRAM_BOT_TOKEN is not set!"
            logger.error(msg)
            raise SystemExit(msg)
        if not TELEGRAM_CHAT_ID:
            msg = "TELEGRAM_CHAT_ID is not set!"
            logger.error(msg)
            raise SystemExit(msg)

        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID

    def send_message(self, msg: str) -> None:
        try:
            self.bot.send_message(chat_id=self.chat_id, text=msg)
        except Exception as e:
            logger.error("[telegram] error: %s", e)
