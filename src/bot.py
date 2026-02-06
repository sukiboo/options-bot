from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.alpaca_client import AlpacaClient
from src.schemas import AlpacaEnv, Settings, TelegramEnv
from src.telegram_bot import TelegramBot

logger = logging.getLogger()


class OptionsBot:
    notify_on_check = False
    notify_on_trade = True

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
        logger.info(f"Scheduling checks: '{self.settings.check_schedule}' ({self.settings.tz})")
        self.scheduler.add_job(
            self.run_checks,
            CronTrigger.from_crontab(self.settings.check_schedule, timezone=self.settings.tz),
        )

        logger.info(f"Scheduling trades: '{self.settings.trade_schedule}' ({self.settings.tz})")
        self.scheduler.add_job(
            self.run_trades,
            CronTrigger.from_crontab(self.settings.trade_schedule, timezone=self.settings.tz),
        )

        self.scheduler.start()

    def run_checks(self) -> None:
        now = datetime.now(self.settings.tz).strftime("%H:%M:%S")
        logger.debug(f"Executing checking tasks at {now}...")
        try:
            self.report_positions(telegram=self.notify_on_check)
            self.report_value(telegram=self.notify_on_check)
            logger.debug("Successfully completed all checking tasks!")
        except Exception as e:
            error_msg = f"Error during checking execution: {e}"
            logger.error(error_msg)
            self.telegram_bot.send_message(msg=f"⚠️ {error_msg}")

    def run_trades(self) -> None:
        now = datetime.now(self.settings.tz).strftime("%H:%M:%S")
        logger.debug(f"Executing trading tasks at {now}...")
        try:
            self.trade_options(telegram=self.notify_on_trade)
            logger.debug("Successfully completed all trading tasks!")
        except Exception as e:
            error_msg = f"Error during trading execution: {e}"
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
