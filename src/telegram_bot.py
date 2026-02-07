from __future__ import annotations

import asyncio
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
            asyncio.run(self._send(msg, silent))
        except Exception as e:
            logger.error("[telegram] error: %s", e)

    async def _send(self, msg: str, silent: bool) -> None:
        async with self.bot:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"<code>{html.escape(msg)}</code>",
                parse_mode="HTML",
                disable_notification=silent,
            )
