from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import cast

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    AssetClass,
    ContractType,
    OrderSide,
    OrderStatus,
    TimeInForce,
)
from alpaca.trading.models import OptionContract, Order, Position, TradeAccount
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest

from src.schemas import AlpacaEnv, Settings

logger = logging.getLogger()


class AlpacaClient:
    def __init__(self, env: AlpacaEnv, settings: Settings) -> None:
        self.settings = settings
        self.client = TradingClient(env.api_key, env.api_secret, paper=settings.paper_trading)
        self.data_client = StockHistoricalDataClient(env.api_key, env.api_secret)
        self.get_ticker_price(settings.ticker)  # validate ticker

    @property
    def account(self) -> TradeAccount:
        account = self.client.get_account()
        if not isinstance(account, TradeAccount):
            raise TypeError(f"Expected TradeAccount, got {type(account).__name__}")
        return cast(TradeAccount, account)

    @property
    def positions(self) -> dict[str, dict[str, str | None]]:
        ticker = self.settings.ticker
        return {
            **{str(self.account.currency): {"qty": str(self.account.cash), "price": "1.00"}},
            **{ticker: {"qty": "0", "price": str(self.get_ticker_price(ticker))}},
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

    def trade_options(self) -> dict | None:
        ticker = self.settings.ticker
        if self.have_option_contracts(ticker):
            logger.debug("Options are in portfolio already, skipping options trade.")
            return None

        expiration_date = self.get_expiration_date()
        ticker_price = self.get_ticker_price(ticker)

        if float(self.positions.get(ticker, {}).get("qty") or "0") > 0:
            strike_price = (1 + self.settings.call_option_margin) * ticker_price
            order = self.sell_covered_calls(ticker, expiration_date, strike_price)
            option_type = "call"
        else:
            strike_price = (1 - self.settings.put_option_margin) * ticker_price
            order = self.sell_covered_puts(ticker, expiration_date, strike_price)
            option_type = "put"

        if order is None:
            return None

        filled_order = self.wait_for_fill(order)
        return {
            "type": option_type,
            "symbol": filled_order.symbol,
            "qty": filled_order.qty,
            "filled_avg_price": filled_order.filled_avg_price,
            "status": str(filled_order.status),
        }

    def sell_covered_calls(
        self, ticker: str, expiration_date: date, strike_price: float
    ) -> Order | None:
        ticker_qty = float(self.positions[ticker]["qty"] or "0")
        if ticker_qty < 100:
            logger.debug(
                f"Only have {ticker_qty} shares of {ticker}, "
                f"not enough for the covered call trade."
            )
            return None

        call_contract_qty = int(ticker_qty / 100)
        call_contract = self.get_option_contract(
            ticker, expiration_date, strike_price, ContractType.CALL
        )

        logger.debug(f"Selling {call_contract_qty} calls for {ticker}: {call_contract}")
        return self.submit_sell_order(call_contract.symbol, call_contract_qty)

    def sell_covered_puts(
        self, ticker: str, expiration_date: date, strike_price: float
    ) -> Order | None:
        cash = float(self.positions["USD"]["qty"] or "0")
        if cash < 100 * strike_price:
            logger.debug(
                f"Only have cash for {cash / strike_price:.2f} shares "
                f"of {ticker}, not enough for the covered put trade."
            )
            return None

        put_contract_qty = int(cash / strike_price / 100)
        put_contract = self.get_option_contract(
            ticker, expiration_date, strike_price, ContractType.PUT
        )

        logger.debug(f"Selling {put_contract_qty} puts for {ticker}: {put_contract}")
        return self.submit_sell_order(put_contract.symbol, put_contract_qty)

    def submit_sell_order(self, symbol: str, qty: int) -> Order:
        logger.info(f"Selling {qty} of {symbol}...")
        order = cast(
            Order,
            self.client.submit_order(
                MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                )
            ),
        )
        logger.info(f"Order submitted: {order.id}")
        return order

    def wait_for_fill(self, order: Order, timeout: int = 60, poll_interval: int = 2) -> Order:
        start = time.time()
        while time.time() - start < timeout:
            order = cast(Order, self.client.get_order_by_id(order.id))
            if order.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
                logger.info(f"Order {order.id} filled at {order.filled_avg_price}")
                return order
            time.sleep(poll_interval)
        logger.warning(f"Order {order.id} not filled within {timeout}s, status: {order.status}")
        return order
