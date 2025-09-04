from __future__ import annotations

import time
from datetime import datetime

import schedule

from src.alpaca_client import AlpacaClient
from src.constants import BOT_NAME
from src.telegram_bot import TelegramBot
from src.utils import get_timezone, parse_run_times, setup_logger

logger = setup_logger()


class OptionsBot:
    def __init__(self) -> None:
        logger.debug(f"{BOT_NAME} initializing...")
        self.setup()
        self.run()

    def setup(self) -> None:
        try:
            self.run_times = parse_run_times()
            self.timezone = get_timezone()
        except ValueError as e:
            logger.error(str(e))
            return

        self.telegram_bot = TelegramBot()
        self.alpaca_client = AlpacaClient()
        self.telegram_bot.send_message(msg=f"{BOT_NAME} is running!")

    def run(self) -> None:
        logger.debug(f"Scheduling tasks for times: {self.run_times} {self.timezone}")
        for run_time in self.run_times:
            schedule.every().day.at(run_time, self.timezone.zone).do(self._run_tasks, run_time)
        while True:
            schedule.run_pending()
            time.sleep(10)

    def _run_tasks(self, run_time: str) -> None:
        logger.debug(
            f"Executing daily tasks at"
            f"{datetime.now(self.timezone).strftime('%H:%M:%S')}"
            f"(scheduled for {run_time})..."
        )
        try:
            self.report_positions()
            self.report_value()
            self.trade_options()
            logger.debug(f"Successfully completed all tasks for {run_time}!")
        except Exception as e:
            error_msg = f"Error during daily tasks execution at {run_time}: {e}"
            logger.error(error_msg)
            self.telegram_bot.send_message(msg=f"⚠️ {error_msg}")

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
