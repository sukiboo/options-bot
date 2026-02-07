from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.alpaca_client import AlpacaClient
from src.schemas import AlpacaEnv, Settings, TelegramEnv
from src.telegram_bot import TelegramBot

logger = logging.getLogger()


class OptionsBot:
    notify_on_trade = True
    notify_on_check = False

    def __init__(
        self, settings: Settings, alpaca_env: AlpacaEnv, telegram_env: TelegramEnv
    ) -> None:
        self.settings = settings
        logger.debug(f"{settings.bot_name} initializing...")
        self.telegram_bot = TelegramBot(telegram_env)
        self.alpaca_client = AlpacaClient(alpaca_env, settings)
        self.scheduler = BlockingScheduler(timezone=settings.tz)
        self.telegram_bot.send_message(msg=f"🔆 {settings.bot_name} is running!")

    def run(self) -> None:
        logger.info(
            f"Schedule trade_options: '{self.settings.trade_options_schedule}' ({self.settings.tz})"
        )
        self.scheduler.add_job(
            self.run_trade_options,
            CronTrigger.from_crontab(
                self.settings.trade_options_schedule, timezone=self.settings.tz
            ),
        )

        logger.info(
            f"Schedule check_value: '{self.settings.check_value_schedule}' ({self.settings.tz})"
        )
        self.scheduler.add_job(
            self.run_check_value,
            CronTrigger.from_crontab(self.settings.check_value_schedule, timezone=self.settings.tz),
        )

        self.scheduler.start()

    def run_trade_options(self) -> None:
        try:
            self.trade_options(telegram=self.notify_on_trade)
        except Exception as e:
            error_msg = f"Error during trade_options: {e}"
            logger.error(error_msg)
            self.telegram_bot.send_message(msg=f"⚠️ {error_msg}")

    def run_check_value(self) -> None:
        try:
            self.report_value(telegram=self.notify_on_check)
        except Exception as e:
            error_msg = f"Error during check_value: {e}"
            logger.error(error_msg)
            self.telegram_bot.send_message(msg=f"⚠️ {error_msg}")

    def report_positions(self, telegram: bool = False) -> None:
        positions = self.alpaca_client.positions
        logger.info(f"positions: {positions}")
        if telegram:
            self.telegram_bot.send_message(msg=f"📑 positions: {positions}")

    def report_value(self, telegram: bool = False) -> None:
        value = self.alpaca_client.portfolio_value
        logger.info(f"portfolio value: ${value:,.2f}")
        if telegram:
            self.telegram_bot.send_message(msg=f"💰 portfolio value: ${value:,.2f}")

    def trade_options(self, telegram: bool = False) -> None:
        if self.alpaca_client.trade_options():
            self.report_positions(telegram=telegram)
            self.report_value(telegram=telegram)
