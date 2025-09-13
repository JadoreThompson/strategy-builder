import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.core.enums import Side, OrderType, PositionStatus
from src.lib.exchanges.backtest_futures_exchange import BacktestFuturesExchange
from src.lib.typing import Tick, Position


@pytest.fixture
def sample_df():
    """Creates a sample pandas DataFrame for testing."""
    data = {"close": [100.0, 101.0, 102.0, 103.0, 99.0]}
    index = pd.to_datetime(
        [
            "2023-01-01 12:00",
            "2023-01-01 12:01",
            "2023-01-01 12:02",
            "2023-01-01 12:03",
            "2023-01-01 12:04",
        ]
    )
    return pd.DataFrame(data, index=index)


@patch("src.lib.exchanges.backtest_futures_exchange.Tick", Tick)
def test_subscribe_from_df(sample_df):
    """Tests yielding ticks from a DataFrame."""
    exchange = BacktestFuturesExchange({}, df=sample_df)
    ticks = list(exchange.subscribe("ANY"))

    assert len(ticks) == 5
    assert all(isinstance(tick, Tick) for tick in ticks)
    assert ticks[0].last == 100.0
    assert ticks[4].last == 99.0
    assert exchange.last_tick.last == 99.0


def test_subscribe_from_path(tmp_path):
    """Tests yielding ticks from a CSV file path."""
    csv_file = tmp_path / "data.csv"
    data = {"close": [10, 20]}
    index = pd.to_datetime(["2023-01-01 12:00", "2023-01-01 12:01"])
    pd.DataFrame(data, index=index).to_csv(csv_file)

    exchange = BacktestFuturesExchange({}, df_path=str(csv_file))
    ticks = list(exchange.subscribe("ANY"))

    assert len(ticks) == 2
    assert ticks[0].last == 10
    assert ticks[1].last == 20


@patch("src.lib.exchanges.backtest_futures_exchange.OrderType", OrderType)
def test_open_position_market():
    """Tests opening a valid market order."""
    exchange = BacktestFuturesExchange({}, df=pd.DataFrame({"close": [100.0]}))
    next(exchange.subscribe("ANY"))  # Set last_tick

    pos = exchange.open_position("EURUSD", Side.BID, OrderType.MARKET, Decimal("1.0"))
    assert pos.status.value == PositionStatus.OPEN.value
    assert pos.price == 100.0
    assert pos.order_type.value == OrderType.MARKET.value


@pytest.mark.parametrize(
    "side, order_type, entry_price, current_price, is_valid",
    [
        (Side.BID, OrderType.LIMIT, 95.0, 100.0, True),  # Buy limit below market, valid
        (
            Side.BID,
            OrderType.LIMIT,
            105.0,
            100.0,
            False,
        ),  # Buy limit above market, invalid
        (
            Side.ASK,
            OrderType.LIMIT,
            105.0,
            100.0,
            True,
        ),  # Sell limit above market, valid
        (
            Side.ASK,
            OrderType.LIMIT,
            95.0,
            100.0,
            False,
        ),  # Sell limit below market, invalid
        # Stop Orders
        (Side.BID, OrderType.STOP, 105.0, 100.0, True),  # Buy stop above market, valid
        (
            Side.BID,
            OrderType.STOP,
            95.0,
            100.0,
            False,
        ),  # Buy stop below market, invalid
        (Side.ASK, OrderType.STOP, 95.0, 100.0, True),  # Sell stop below market, valid
        (
            Side.ASK,
            OrderType.STOP,
            105.0,
            100.0,
            False,
        ),  # Sell stop above market, invalid
    ],
)
@patch("src.lib.exchanges.backtest_futures_exchange.OrderType", OrderType)
@patch("src.lib.exchanges.backtest_futures_exchange.Side", Side)
def test_open_position_pending_orders(
    side, order_type, entry_price, current_price, is_valid
):
    """Tests validation for limit and stop orders."""
    exchange = BacktestFuturesExchange({}, df=pd.DataFrame({"close": [current_price]}))
    next(exchange.subscribe("ANY"))

    kwargs = {}
    if order_type == OrderType.LIMIT:
        kwargs["limit_price"] = entry_price
    else:
        kwargs["stop_price"] = entry_price

    pos = exchange.open_position("EURUSD", side, order_type, Decimal("1.0"), **kwargs)

    if is_valid:
        assert pos.status.value == PositionStatus.PENDING.value
    else:
        assert pos is None


@pytest.mark.parametrize(
    "side, open_price, sl, tp, is_valid",
    [
        (Side.BID, 100, 90, 110, True),  # Valid long
        (Side.BID, 100, 110, 120, False),  # Invalid long (SL > open)
        (Side.BID, 100, 90, 80, False),  # Invalid long (TP < open)
        (Side.ASK, 100, 110, 90, True),  # Valid short
        (Side.ASK, 100, 90, 80, False),  # Invalid short (SL < open)
        (Side.ASK, 100, 110, 120, False),  # Invalid short (TP > open)
    ],
)
@patch("src.lib.exchanges.backtest_futures_exchange.OrderType", OrderType)
@patch("src.lib.exchanges.backtest_futures_exchange.Side", Side)
def test_open_position_sl_tp_validation(side, open_price, sl, tp, is_valid):
    """Tests stop loss and take profit validation."""
    exchange = BacktestFuturesExchange({}, df=pd.DataFrame({"close": [open_price]}))
    next(exchange.subscribe("ANY"))

    pos = exchange.open_position(
        "EURUSD", side, OrderType.MARKET, Decimal("1.0"), sl_price=sl, tp_price=tp
    )

    if is_valid:
        assert pos is not None
    else:
        assert pos is None


def test_modify_position_success():
    """Tests a successful position modification."""
    exchange = BacktestFuturesExchange({}, df=pd.DataFrame({"close": [100.0]}))
    next(exchange.subscribe("ANY"))

    initial_pos = Position(
        id="1",
        instrument="EURUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        price=95.0,
        starting_amount=Decimal("1.0"),
    )

    success, updated_pos = exchange.modify_position(
        initial_pos, sl_price=90.0, tp_price=110.0
    )

    assert success is True
    assert updated_pos.sl_price == 90.0
    assert updated_pos.tp_price == 110.0
    assert updated_pos.position_id == initial_pos.id


@patch("src.lib.exchanges.backtest_futures_exchange.OrderType", OrderType)
@patch("src.lib.exchanges.backtest_futures_exchange.Side", Side)
def test_modify_position_failure_invalid_sl_tp():
    """Tests a failed position modification due to invalid SL/TP logic."""
    exchange = BacktestFuturesExchange({}, df=pd.DataFrame({"close": [100.0]}))
    next(exchange.subscribe("ANY"))

    initial_pos = Position(
        id="1",
        instrument="EURUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        price=95.0,
        starting_amount=Decimal("1.0"),
    )

    success, updated_pos = exchange.modify_position(
        initial_pos, sl_price=100.0, tp_price=90.0
    )

    assert success is False
    assert updated_pos is initial_pos  # Should return the original position
