from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.schemas import AlpacaEnv, Settings

SETTINGS_KWARGS = {
    "ticker": "AAPL",
    "call_option_margin": 0.05,
    "put_option_margin": 0.05,
    "trade_options_schedule": "59 9 * * 1-5",
    "check_value_schedule": "0 10-16 * * 1-5",
}
ENV = AlpacaEnv(api_key="fake", api_secret="fake")


def make_client(settings_overrides=None):
    from src.alpaca_client import AlpacaClient

    s = Settings(**{**SETTINGS_KWARGS, **(settings_overrides or {})})
    with patch.object(AlpacaClient, "__init__", lambda self, *a, **kw: None):
        client = AlpacaClient.__new__(AlpacaClient)
        client.settings = s
        client.client = MagicMock()
        client.data_client = MagicMock()
    return client


class TestGetExpirationDate:
    @pytest.mark.parametrize(
        "today, expected",
        [
            (date(2025, 9, 22), date(2025, 9, 26)),  # Monday -> Friday
            (date(2025, 9, 23), date(2025, 9, 26)),  # Tuesday -> Friday
            (date(2025, 9, 24), date(2025, 9, 26)),  # Wednesday -> Friday
            (date(2025, 9, 25), date(2025, 9, 26)),  # Thursday -> Friday
            (date(2025, 9, 26), date(2025, 10, 3)),  # Friday -> next Friday
            (date(2025, 9, 27), date(2025, 10, 3)),  # Saturday -> next Friday
            (date(2025, 9, 28), date(2025, 10, 3)),  # Sunday -> next Friday
        ],
    )
    def test_expiration_date(self, today, expected):
        client = make_client()
        with patch("src.alpaca_client.date") as mock_date:
            mock_date.today.return_value = today
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            assert client.get_expiration_date() == expected


class TestStrikePriceCalculation:
    def test_call_strike_price(self):
        margin = 0.05
        ticker_price = 200.0
        expected = (1 + margin) * ticker_price
        assert expected == 210.0

    def test_put_strike_price(self):
        margin = 0.05
        ticker_price = 200.0
        expected = (1 - margin) * ticker_price
        assert expected == 190.0

    def test_call_contract_qty(self):
        assert int(300 / 100) == 3
        assert int(150 / 100) == 1
        assert int(99 / 100) == 0

    def test_put_contract_qty(self):
        cash = 50000.0
        strike = 190.0
        assert int(cash / strike / 100) == 2


class TestSellCoveredCalls:
    def test_not_enough_shares(self):
        from src.alpaca_client import AlpacaClient

        client = make_client()
        positions = {"AAPL": {"qty": "50", "price": "200.0"}}
        with patch.object(
            AlpacaClient, "positions", new_callable=PropertyMock, return_value=positions
        ):
            result = client.sell_covered_calls("AAPL", date(2025, 9, 26), 210.0)
        assert result is None

    def test_enough_shares(self):
        from src.alpaca_client import AlpacaClient

        client = make_client()
        positions = {"AAPL": {"qty": "200", "price": "200.0"}}

        mock_contract = MagicMock()
        mock_contract.symbol = "AAPL250926C00210000"
        client.get_option_contract = MagicMock(return_value=mock_contract)
        client.submit_sell_order = MagicMock()

        with patch.object(
            AlpacaClient, "positions", new_callable=PropertyMock, return_value=positions
        ):
            client.sell_covered_calls("AAPL", date(2025, 9, 26), 210.0)
        client.submit_sell_order.assert_called_once_with("AAPL250926C00210000", 2)


class TestSellCoveredPuts:
    def test_not_enough_cash(self):
        from src.alpaca_client import AlpacaClient

        client = make_client()
        positions = {"USD": {"qty": "1000", "price": "1.00"}}
        with patch.object(
            AlpacaClient, "positions", new_callable=PropertyMock, return_value=positions
        ):
            result = client.sell_covered_puts("AAPL", date(2025, 9, 26), 190.0)
        assert result is None

    def test_enough_cash(self):
        from src.alpaca_client import AlpacaClient

        client = make_client()
        positions = {"USD": {"qty": "50000", "price": "1.00"}}

        mock_contract = MagicMock()
        mock_contract.symbol = "AAPL250926P00190000"
        client.get_option_contract = MagicMock(return_value=mock_contract)
        client.submit_sell_order = MagicMock()

        with patch.object(
            AlpacaClient, "positions", new_callable=PropertyMock, return_value=positions
        ):
            client.sell_covered_puts("AAPL", date(2025, 9, 26), 190.0)
        client.submit_sell_order.assert_called_once_with("AAPL250926P00190000", 2)
