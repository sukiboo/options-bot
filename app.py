from __future__ import annotations

from src.alpaca_client import AlpacaClient
from src.constants import BOT_NAME
from src.telegram_bot import TelegramBot
from src.utils import setup_logger

logger = setup_logger()


class OptionsBot:
    def __init__(self) -> None:
        logger.info(f"{BOT_NAME} initializing...")
        self.setup()
        self.report()

    def setup(self) -> None:
        self.telegram_bot = TelegramBot()
        self.alpaca_client = AlpacaClient()
        self.telegram_bot.send_message(msg=f"{BOT_NAME} is running!")

    def report(self) -> None:
        value = self.alpaca_client.get_portfolio_value()
        positions = self.alpaca_client.get_positions()
        self.telegram_bot.send_message(msg=f"portfolio value: ${value:,.2f}")
        self.telegram_bot.send_message(msg=f"positions: {positions}")


if __name__ == "__main__":
    bot = OptionsBot()
