from __future__ import annotations

import logging
import os
import time
from datetime import date, timedelta
from typing import cast

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass, ContractType, OrderSide, TimeInForce
from alpaca.trading.models import OptionContract, Position, TradeAccount
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest

from src.constants import (
    OTM_MARGIN_CALL,
    OTM_MARGIN_PUT,
    PAPER_TRADING,
    POST_TRADE_DELAY,
    TICKER,
)

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
        self.data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)

    @property
    def account(self) -> TradeAccount:
        account = self.client.get_account()
        if not isinstance(account, TradeAccount):
            raise TypeError(f"Expected TradeAccount, got {type(account).__name__}")
        return cast(TradeAccount, account)

    @property
    def positions(self) -> dict[str, dict[str, str | None]]:
        return {
            **{str(self.account.currency): {"qty": str(self.account.cash), "price": "1.00"}},
            **{
                str(p.symbol): {"qty": str(p.qty), "price": str(p.current_price)}
                for p in cast(list[Position], self.client.get_all_positions())
            },
        }

    @property
    def portfolio_value(self) -> float:
        portfolio_value = self.account.equity
        if portfolio_value is None:
            raise RuntimeError("Portfolio value is unavailable!")
        return float(portfolio_value)

    def get_ticker_price(self, ticker: str) -> float:
        latest_trade = self.data_client.get_stock_latest_trade(
            StockLatestTradeRequest(symbol_or_symbols=ticker)
        ).get(ticker)
        ticker_price = latest_trade.price if latest_trade else None
        logger.debug(f"Ticker price for `{ticker}`: {ticker_price}")
        if ticker_price is None:
            raise RuntimeError(f"Ticker price is unavailable for `{ticker}`!")
        return ticker_price

    def get_expiration_date(self) -> date:
        """Return the next Friday expiration date."""
        return date.today() + timedelta(days=(4 - date.today().weekday()) % 7 or 7)

    def have_option_contracts(self, ticker: str) -> bool:
        return any(
            p.symbol.startswith(ticker) and p.asset_class == AssetClass.US_OPTION
            for p in cast(list[Position], self.client.get_all_positions())
        )

    def get_option_contract(
        self,
        ticker: str,
        expiration_date: date,
        price_gte: float,
        option_type: ContractType,
    ) -> OptionContract:
        contracts = self.client.get_option_contracts(
            GetOptionContractsRequest(
                underlying_symbols=[ticker],
                expiration_date=expiration_date,
                type=option_type,
                strike_price_gte=str(price_gte),
                limit=1000,
            )
        )

        if contracts is None or not hasattr(contracts, "option_contracts"):
            raise RuntimeError(f"Option contracts are unavailable for `{ticker}`!")

        option_contracts = getattr(contracts, "option_contracts", [])
        if not option_contracts:
            raise RuntimeError(f"No option contracts found for `{ticker}`!")

        return option_contracts[0]

    def trade_options(self) -> bool:
        if self.have_option_contracts(TICKER):
            logger.debug("Options are in portfolio already, skipping options trade.")
            return False

        expiration_date = self.get_expiration_date()
        ticker_price = self.get_ticker_price(TICKER)

        if TICKER in self.positions:
            strike_price = (1 + OTM_MARGIN_CALL) * ticker_price
            self.sell_covered_calls(TICKER, expiration_date, strike_price)
        else:
            strike_price = (1 - OTM_MARGIN_PUT) * ticker_price
            self.sell_covered_puts(TICKER, expiration_date, strike_price)

        time.sleep(POST_TRADE_DELAY)

        return True

    def sell_covered_calls(self, ticker: str, expiration_date: date, strike_price: float) -> None:
        ticker_qty = int(self.positions[ticker]["qty"] or "0")
        if ticker_qty < 100:
            logger.debug(
                f"Only have {ticker_qty} shares of {ticker}, "
                f"not enough for the covered call trade."
            )
            return

        call_contract_qty = int(ticker_qty / 100)
        call_contract = self.get_option_contract(
            ticker, expiration_date, strike_price, ContractType.CALL
        )

        logger.debug(f"Selling {call_contract_qty} calls for {ticker}: {call_contract}")
        self.submit_sell_order(call_contract.symbol, call_contract_qty)

    def sell_covered_puts(self, ticker: str, expiration_date: date, strike_price: float) -> None:
        cash = int(self.positions["USD"]["qty"] or "0")
        if cash < 100 * strike_price:
            logger.debug(
                f"Only have cash for {cash / strike_price:.2f} shares "
                f"of {ticker}, not enough for the covered put trade."
            )
            return

        put_contract_qty = int(cash / strike_price / 100)
        put_contract = self.get_option_contract(
            ticker, expiration_date, strike_price, ContractType.PUT
        )

        logger.debug(f"Selling {put_contract_qty} puts for {ticker}: {put_contract}")
        self.submit_sell_order(put_contract.symbol, put_contract_qty)

    def submit_sell_order(self, symbol: str, qty: int) -> None:
        logger.info(f"Selling {qty} shares of {symbol}...")
        order = self.client.submit_order(
            MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
        )
        if order:
            logger.info(f"Order submitted successfully: {order}")
        else:
            logger.error(f"Order submission failed: {order}")
