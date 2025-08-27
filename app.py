from __future__ import annotations

from datetime import datetime, timezone

from src.constants import BOT_NAME
from src.telegram_bot import TelegramBot
from src.utils import setup_logger

logger = setup_logger()


class OptionsBot:
    def __init__(self) -> None:
        logger.info(f"{BOT_NAME} initializing...")
        self.telegram_bot = TelegramBot()
        self.telegram_bot.send_message(
            msg=f"{BOT_NAME} started at {datetime.now(timezone.utc).isoformat()}"
        )


if __name__ == "__main__":
    bot = OptionsBot()
