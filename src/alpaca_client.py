from __future__ import annotations

import logging
import os
from functools import cached_property
from typing import cast

from alpaca.trading.client import TradingClient
from alpaca.trading.models import TradeAccount

from src.constants import PAPER_TRADING

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET", "")


logger = logging.getLogger()


class AlpacaClient:
    def __init__(self) -> None:
        self.setup()

    def setup(self) -> None:
        if not ALPACA_API_KEY:
            msg = "ALPACA_API_KEY is not set!"
            logger.error(msg)
            raise SystemExit(msg)
        if not ALPACA_API_SECRET:
            msg = "ALPACA_API_SECRET is not set!"
            logger.error(msg)
            raise SystemExit(msg)

        self.client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=PAPER_TRADING)

    @cached_property
    def account(self) -> TradeAccount:
        acct = self.client.get_account()
        if not isinstance(acct, TradeAccount):
            raise TypeError(f"Expected TradeAccount, got {type(acct).__name__}")
        return cast(TradeAccount, acct)

    def refresh_account(self) -> None:
        self.__dict__.pop("account", None)

    def get_portfolio_value(self) -> float:
        portfolio_value = self.account.equity
        if portfolio_value is None:
            raise RuntimeError("Portfolio value is unavailable!")
        self.refresh_account()
        return float(portfolio_value)
