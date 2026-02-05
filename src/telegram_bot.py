from __future__ import annotations

import logging

import telegram

from src.schemas import TelegramEnv

logger = logging.getLogger()


class TelegramBot:
    def __init__(self, env: TelegramEnv) -> None:
        self.bot = telegram.Bot(token=env.bot_token)
        self.chat_id = env.chat_id

    def send_message(self, msg: str) -> None:
        try:
            self.bot.send_message(chat_id=self.chat_id, text=msg)
        except Exception as e:
            logger.error("[telegram] error: %s", e)
