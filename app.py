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
        self.report_positions()
        self.report_value()

    def setup(self) -> None:
        self.telegram_bot = TelegramBot()
        self.alpaca_client = AlpacaClient()
        self.telegram_bot.send_message(msg=f"{BOT_NAME} is running!")

    def report_positions(self) -> None:
        positions = self.alpaca_client.positions
        logger.info(f"positions: {positions}")
        self.telegram_bot.send_message(msg=f"positions: {positions}")

    def report_value(self) -> None:
        value = self.alpaca_client.portfolio_value
        logger.info(f"portfolio value: ${value:,.2f}")
        self.telegram_bot.send_message(msg=f"portfolio value: ${value:,.2f}")

    def trade_options(self) -> None:
        self.alpaca_client.trade_options()
        self.report_positions()


if __name__ == "__main__":
    bot = OptionsBot()
