from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.schemas import (
    AlpacaEnv,
    Settings,
    TelegramEnv,
    load_alpaca_env,
    load_settings,
    load_telegram_env,
)

VALID_SETTINGS = {
    "ticker": "AAPL",
    "call_option_margin": 0.05,
    "put_option_margin": 0.05,
    "trade_options_schedule": "59 9 * * 1-5",
    "check_value_schedule": "0 10-16 * * 1-5",
}


class TestSettings:
    def test_valid_settings(self):
        s = Settings(**VALID_SETTINGS)
        assert s.ticker == "AAPL"
        assert s.paper_trading is True
        assert s.bot_name == "options-bot"

    def test_timezone_default(self):
        s = Settings(**VALID_SETTINGS)
        assert s.timezone == "America/New_York"
        assert s.tz.zone == "America/New_York"

    def test_timezone_valid(self):
        s = Settings(**{**VALID_SETTINGS, "timezone": "UTC"})
        assert s.timezone == "UTC"

    def test_timezone_invalid(self):
        with pytest.raises(ValidationError, match="Unknown timezone"):
            Settings(**{**VALID_SETTINGS, "timezone": "Not/A/Timezone"})

    def test_timezone_empty(self):
        with pytest.raises(ValidationError, match="Unknown timezone"):
            Settings(**{**VALID_SETTINGS, "timezone": ""})

    def test_cron_valid(self):
        s = Settings(**{**VALID_SETTINGS, "trade_options_schedule": "0 12 * * *"})
        assert s.trade_options_schedule == "0 12 * * *"

    def test_cron_invalid(self):
        with pytest.raises(ValidationError, match="Invalid cron pattern"):
            Settings(**{**VALID_SETTINGS, "trade_options_schedule": "not a cron"})

    def test_margin_bounds(self):
        Settings(**{**VALID_SETTINGS, "call_option_margin": 0.99})
        Settings(**{**VALID_SETTINGS, "call_option_margin": -0.99})

    def test_margin_out_of_range(self):
        with pytest.raises(ValidationError):
            Settings(**{**VALID_SETTINGS, "call_option_margin": 1.0})
        with pytest.raises(ValidationError):
            Settings(**{**VALID_SETTINGS, "put_option_margin": -1.0})

    def test_missing_ticker(self):
        data = {**VALID_SETTINGS}
        del data["ticker"]
        with pytest.raises(ValidationError):
            Settings(**data)


class TestLoadSettings:
    def test_missing_file(self):
        with pytest.raises(SystemExit, match="not found"):
            load_settings("nonexistent.yaml")

    def test_valid_file(self, tmp_path):
        p = tmp_path / "settings.yaml"
        p.write_text(
            "ticker: SPY\n"
            "call_option_margin: 0.03\n"
            "put_option_margin: 0.03\n"
            "trade_options_schedule: '0 10 * * 1-5'\n"
            "check_value_schedule: '0 16 * * 1-5'\n"
        )
        s = load_settings(str(p))
        assert s.ticker == "SPY"
        assert s.call_option_margin == 0.03


class TestLoadEnvs:
    def test_load_alpaca_env(self):
        with patch.dict(os.environ, {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s"}):
            env = load_alpaca_env()
            assert env == AlpacaEnv(api_key="k", api_secret="s")

    def test_load_alpaca_env_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit, match="ALPACA_API_KEY"):
                load_alpaca_env()

    def test_load_telegram_env(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "c"}):
            env = load_telegram_env()
            assert env == TelegramEnv(bot_token="t", chat_id="c")

    def test_load_telegram_env_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit, match="TELEGRAM_BOT_TOKEN"):
                load_telegram_env()
