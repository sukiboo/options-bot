from __future__ import annotations

import html
import logging

import telegram

from src.schemas import TelegramEnv

logger = logging.getLogger()


class TelegramBot:
    def __init__(self, env: TelegramEnv) -> None:
        self.bot = telegram.Bot(token=env.bot_token)
        self.chat_id = env.chat_id

    def send_message(self, msg: str, silent: bool = False) -> None:
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=f"<code>{html.escape(msg)}</code>",
                parse_mode="HTML",
                disable_notification=silent,
            )
        except Exception as e:
            logger.error("[telegram] error: %s", e)
