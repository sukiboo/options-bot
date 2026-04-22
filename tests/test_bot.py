from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock

from src.bot import OptionsBot


def make_bot(currency: str = "USD", positions: dict | None = None):
    bot = OptionsBot.__new__(OptionsBot)
    bot.telegram_bot = MagicMock()
    bot.alpaca_client = MagicMock()
    bot.alpaca_client.account.currency = currency
    bot.alpaca_client.positions = positions or {}
    return bot


class TestReportTrade:
    def _trade(self, side: str) -> dict:
        return {
            "type": "call",
            "side": side,
            "symbol": "AAPL250926C00210000",
            "qty": 2,
            "filled_avg_price": 1.23,
            "status": "filled",
        }

    def test_sell_renders_side_verbatim(self):
        bot = make_bot()
        bot.report_trade(self._trade("sell"), telegram=True)
        msg = bot.telegram_bot.send_message.call_args.kwargs["msg"]
        assert "sell AAPL250926C00210000" in msg

    def test_buy_renders_side_verbatim(self):
        bot = make_bot()
        bot.report_trade(self._trade("buy"), telegram=True)
        msg = bot.telegram_bot.send_message.call_args.kwargs["msg"]
        assert "buy AAPL250926C00210000" in msg

    def test_no_telegram_when_disabled(self):
        bot = make_bot()
        bot.report_trade(self._trade("sell"), telegram=False)
        bot.telegram_bot.send_message.assert_not_called()

    def test_log_is_json(self, caplog):
        bot = make_bot()
        with caplog.at_level(logging.INFO):
            bot.report_trade(self._trade("sell"), telegram=False)
        assert json.loads(caplog.records[-1].message) == {"trade": self._trade("sell")}


class TestReportPositions:
    def _positions(self) -> dict:
        return {
            "USD": {"qty": "148677.06", "price": "1.00"},
            "SOXL": {"qty": "0", "price": "76.59"},
            "SOXL260417P00073000": {"qty": "-20", "price": "2.62"},
        }

    def test_telegram_message_is_pretty_multiline(self):
        bot = make_bot(positions=self._positions())
        bot.report_positions(telegram=True)
        msg = bot.telegram_bot.send_message.call_args.kwargs["msg"]
        assert msg == (
            "💰 positions: {\n"
            "  USD: $148,677.06,\n"
            "  SOXL: 0 x $76.59,\n"
            "  SOXL260417P00073000: -20 x $2.62,\n"
            "}"
        )

    def test_log_is_json(self, caplog):
        positions = self._positions()
        bot = make_bot(positions=positions)
        with caplog.at_level(logging.INFO):
            bot.report_positions(telegram=False)
        assert json.loads(caplog.records[-1].message) == {"positions": positions}

    def test_no_telegram_when_disabled(self):
        bot = make_bot(positions=self._positions())
        bot.report_positions(telegram=False)
        bot.telegram_bot.send_message.assert_not_called()

    def test_non_usd_currency_treated_as_cash(self):
        bot = make_bot(
            currency="EUR",
            positions={"EUR": {"qty": "1000.00", "price": "1.00"}},
        )
        bot.report_positions(telegram=True)
        msg = bot.telegram_bot.send_message.call_args.kwargs["msg"]
        assert "EUR: $1,000.00," in msg
