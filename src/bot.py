from __future__ import annotations

import json
import logging

from apscheduler.triggers.cron import CronTrigger

from src.alpaca_client import AlpacaClient
from src.schemas import AlpacaEnv, Settings, TelegramEnv
from src.telegram_bot import TelegramBot
from src.utils import SafeBlockingScheduler

logger = logging.getLogger()


def _format_position(symbol: str, data: dict, currency: str) -> str:
    qty = data["qty"] or "0"
    if symbol == currency:
        return f"${float(qty):,.2f}"
    price = float(data["price"] or 0)
    return f"{qty} x ${price:,.2f}"


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
        self.scheduler = SafeBlockingScheduler(timezone=settings.tz)
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

    def trade_options(self, telegram: bool = False) -> None:
        if trade := self.alpaca_client.trade_options():
            self.report_trade(trade, telegram=telegram)
            self.report_positions(telegram=telegram)
            self.report_value(telegram=telegram)

    def report_trade(self, trade: dict, telegram: bool = False) -> None:
        logger.info(json.dumps({"trade": trade}))
        if telegram:
            msg = (
                f"{trade['side']} {trade['symbol']} x {trade['qty']}"
                f" @ ${trade['filled_avg_price']:,.2f}"
            )
            self.telegram_bot.send_message(msg=f"🤝 {msg}")

    def report_positions(self, telegram: bool = False) -> None:
        positions = self.alpaca_client.positions
        logger.info(json.dumps({"positions": positions}))
        if telegram:
            currency = str(self.alpaca_client.account.currency)
            rows = "\n".join(
                f"  {s}: {_format_position(s, d, currency)}," for s, d in positions.items()
            )
            self.telegram_bot.send_message(msg=f"💰 positions: {{\n{rows}\n}}")

    def report_value(self, telegram: bool = False) -> None:
        value = self.alpaca_client.portfolio_value
        logger.info(json.dumps({"portfolio_value": value}))
        if telegram:
            self.telegram_bot.send_message(msg=f"💲 portfolio value: ${value:,.2f}")
