from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Callable

import schedule

from src.alpaca_client import AlpacaClient
from src.schemas import AlpacaEnv, Settings, TelegramEnv
from src.telegram_bot import TelegramBot

logger = logging.getLogger()


class OptionsBot:
    def __init__(
        self, settings: Settings, alpaca_env: AlpacaEnv, telegram_env: TelegramEnv
    ) -> None:
        self.settings = settings
        logger.debug(f"{settings.bot_name} initializing...")
        self.telegram_bot = TelegramBot(telegram_env)
        self.alpaca_client = AlpacaClient(alpaca_env, settings)
        self.telegram_bot.send_message(msg=f"{settings.bot_name} is running!")

    def _schedule_weekday_task(self, task_func: Callable[[str], None], run_time: str) -> None:
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for day in weekdays:
            getattr(schedule.every(), day).at(run_time, self.settings.tz.zone).do(
                task_func, run_time
            )

    def run(self) -> None:
        logger.debug(
            f"Scheduling checking for times: {self.settings.check_times} {self.settings.tz}"
        )
        for run_time in self.settings.check_times:
            self._schedule_weekday_task(self._run_checks, run_time)

        logger.debug(
            f"Scheduling trading for times: {self.settings.trade_times} {self.settings.tz}"
        )
        for run_time in self.settings.trade_times:
            self._schedule_weekday_task(self._run_trades, run_time)

        while True:
            schedule.run_pending()
            time.sleep(10)

    def _run_checks(self, run_time: str) -> None:
        logger.debug(
            f"Executing checking tasks at "
            f"{datetime.now(self.settings.tz).strftime('%H:%M:%S')} "
            f"(scheduled for {run_time})..."
        )
        try:
            self.report_positions(telegram=False)
            self.report_value(telegram=False)
            logger.debug(f"Successfully completed all checking tasks for {run_time}!")
        except Exception as e:
            error_msg = f"Error during checking execution at {run_time}: {e}"
            logger.error(error_msg)
            self.telegram_bot.send_message(msg=f"⚠️ {error_msg}")

    def _run_trades(self, run_time: str) -> None:
        logger.debug(
            f"Executing trading tasks at "
            f"{datetime.now(self.settings.tz).strftime('%H:%M:%S')} "
            f"(scheduled for {run_time})..."
        )
        try:
            self.trade_options(telegram=True)
            logger.debug(f"Successfully completed all trading tasks for {run_time}!")
        except Exception as e:
            error_msg = f"Error during trading execution at {run_time}: {e}"
            logger.error(error_msg)
            self.telegram_bot.send_message(msg=f"⚠️ {error_msg}")

    def report_positions(self, telegram: bool = False) -> None:
        positions = self.alpaca_client.positions
        logger.info(f"positions: {positions}")
        if telegram:
            self.telegram_bot.send_message(msg=f"positions: {positions}")

    def report_value(self, telegram: bool = False) -> None:
        value = self.alpaca_client.portfolio_value
        logger.info(f"portfolio value: ${value:,.2f}")
        if telegram:
            self.telegram_bot.send_message(msg=f"portfolio value: ${value:,.2f}")

    def trade_options(self, telegram: bool = False) -> None:
        if self.alpaca_client.trade_options():
            self.report_positions(telegram=telegram)
            self.report_value(telegram=telegram)
