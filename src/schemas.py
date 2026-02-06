from __future__ import annotations

import os
from pathlib import Path

import pytz  # type: ignore
import yaml
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    bot_name: str = "options-bot"
    paper_trading: bool = True
    post_trade_delay: int = Field(default=60, ge=0)
    ticker: str
    otm_margin_call: float = Field(gt=0, lt=1)
    otm_margin_put: float = Field(gt=0, lt=1)
    timezone: str = "America/New_York"
    trade_schedule: str
    check_schedule: str

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        pytz.timezone(v)
        return v

    @field_validator("trade_schedule", "check_schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        try:
            CronTrigger.from_crontab(v)
        except ValueError as e:
            raise ValueError(f"Invalid cron pattern '{v}': {e}")
        return v

    @property
    def tz(self) -> pytz.BaseTzInfo:
        return pytz.timezone(self.timezone)


class AlpacaEnv(BaseModel):
    api_key: str
    api_secret: str


class TelegramEnv(BaseModel):
    bot_token: str
    chat_id: str


def load_settings(path: str = "settings.yaml") -> Settings:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"{path} not found")
    with p.open() as f:
        return Settings(**yaml.safe_load(f) or {})


def load_alpaca_env() -> AlpacaEnv:
    key = os.getenv("ALPACA_API_KEY", "")
    secret = os.getenv("ALPACA_API_SECRET", "")
    if not key or not secret:
        raise SystemExit("ALPACA_API_KEY and ALPACA_API_SECRET must be set")
    return AlpacaEnv(api_key=key, api_secret=secret)


def load_telegram_env() -> TelegramEnv:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
    return TelegramEnv(bot_token=token, chat_id=chat_id)
