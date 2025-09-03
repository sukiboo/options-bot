from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Literal, cast

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import ContractType, OrderSide, TimeInForce
from alpaca.trading.models import OptionContract, Position, TradeAccount
from alpaca.trading.requests import GetOptionContractsRequest, MarketOrderRequest

from src.constants import OTM_MARGIN_CALL, OTM_MARGIN_PUT, PAPER_TRADING, TICKER

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

    def trade_options(self) -> None:
        if TICKER in self.positions and int(self.positions[TICKER]["qty"] or "0") >= 100:
            self.sell_covered_calls(TICKER)
        else:
            self.sell_covered_puts(TICKER)

    def get_ticker_price(self, ticker: str) -> float:
        latest_trade = self.data_client.get_stock_latest_trade(
            StockLatestTradeRequest(symbol_or_symbols=ticker)
        ).get(ticker)
        ticker_price = latest_trade.price if latest_trade else None
        logger.debug(f"Ticker price for `{ticker}`: {ticker_price}")
        if ticker_price is None:
            raise RuntimeError(f"Ticker price is unavailable for `{ticker}`!")
        return ticker_price

    def get_option_contract(
        self, ticker: str, option_type: Literal["call", "put"]
    ) -> OptionContract:
        expiration_date = date.today() + timedelta(days=(4 - date.today().weekday()) % 7 or 7)
        ticker_price = self.get_ticker_price(ticker)

        if option_type == "call":
            contract_type = ContractType.CALL
            strike_price = (1 + OTM_MARGIN_CALL) * ticker_price
        elif option_type == "put":
            contract_type = ContractType.PUT
            strike_price = (1 - OTM_MARGIN_PUT) * ticker_price
        else:
            raise ValueError(f"Invalid option type: `{option_type}`!")

        contracts = self.client.get_option_contracts(
            GetOptionContractsRequest(
                underlying_symbols=[ticker],
                expiration_date=expiration_date,
                type=contract_type,
                strike_price_gte=str(strike_price),
                limit=1000,
            )
        )

        if contracts is None or not hasattr(contracts, "option_contracts"):
            raise RuntimeError(f"Option contracts are unavailable for `{ticker}`!")

        option_contracts = getattr(contracts, "option_contracts", [])
        if not option_contracts:
            raise RuntimeError(f"No option contracts found for `{ticker}`!")

        return option_contracts[0]

    # TODO: print confirmations
    def sell_covered_calls(self, ticker: str) -> None:
        call_contract = self.get_option_contract(ticker, "call")
        contract_qty = int(self.positions[ticker]["qty"] or "0") // 100
        logger.info(f"Selling {contract_qty} calls for {ticker}:\n{call_contract}")
        self.client.submit_order(
            MarketOrderRequest(
                symbol=call_contract.symbol,
                qty=contract_qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
        )

    # TODO: print confirmations
    def sell_covered_puts(self, ticker: str) -> None:
        put_contract = self.get_option_contract(ticker, "put")
        contract_qty = (
            int(self.positions["USD"]["qty"] or "0") / self.get_ticker_price(ticker) // 100
        )
        logger.info(f"Selling {contract_qty} puts for {ticker}:\n{put_contract}")
        self.client.submit_order(
            MarketOrderRequest(
                symbol=put_contract.symbol,
                qty=contract_qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
        )
