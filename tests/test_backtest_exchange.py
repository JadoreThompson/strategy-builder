from typing import Generator
import pytest
import pandas as pd
from datetime import datetime
from decimal import Decimal
import tempfile
import os

# Import the class to be tested
from lib.exchanges.backtest_futures_exchange import BacktestFuturesExchange
from lib.typing import Tick, Position, MODIFY_SENTINEL
from core.enums import OrderType, Side, PositionStatus
from lib.exchanges.backtest_futures_exchange import (
    SENTINEL_POSITION,
)  # Import the sentinel

# Fixtures from conftest.py
# - sample_df
# - empty_df


@pytest.fixture
def setup_exchange_with_df(sample_df: pd.DataFrame) -> BacktestFuturesExchange:
    """Fixture to setup BacktestFuturesExchange with a DataFrame."""
    exchange = BacktestFuturesExchange(login_creds={}, df=sample_df)
    return exchange


@pytest.fixture
def setup_exchange_with_df_path(
    sample_df: pd.DataFrame,
) -> Generator[BacktestFuturesExchange, None, None]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmpfile:
        sample_df.to_csv(tmpfile.name)
        df_path = tmpfile.name

        exchange = BacktestFuturesExchange(login_creds={}, df_path=df_path)
        yield exchange


def test_backtest_futures_exchange_subscribe_with_df(
    setup_exchange_with_df: BacktestFuturesExchange, sample_df: pd.DataFrame
):
    """Test that subscribe yields correct Ticks from a DataFrame."""
    exchange = setup_exchange_with_df
    instrument = "BTCUSD"
    ticks_generated = list(exchange.subscribe(instrument))

    assert len(ticks_generated) == len(sample_df)

    first_row = sample_df.iloc[0]
    first_tick = ticks_generated[0]
    assert first_tick.last == pytest.approx(first_row["close"])
    assert first_tick.time == first_row.name  # Assuming index is datetime

    last_row = sample_df.iloc[-1]
    last_tick = ticks_generated[-1]
    assert last_tick.last == pytest.approx(last_row["close"])
    assert last_tick.time == last_row.name


def test_backtest_futures_exchange_open_position_market(setup_exchange_with_df):
    """Test opening a MARKET position."""
    exchange = setup_exchange_with_df
    instrument = "BTCUSD"
    side = Side.BID
    order_type = OrderType.MARKET
    amount = Decimal("10")
    price = 10000.50

    position = exchange.open_position(instrument, side, order_type, amount, price=price)

    assert isinstance(position, Position)
    assert position.id is not None and isinstance(position.id, str)
    assert position.instrument == instrument
    assert position.side == side
    assert position.order_type == order_type
    assert position.starting_amount == amount
    assert (
        position.current_amount == amount
    )  # Should be initialized with starting amount
    assert position.price == price
    assert position.status == PositionStatus.OPEN


def test_backtest_futures_exchange_open_position_limit_stop(setup_exchange_with_df):
    """Test opening LIMIT/STOP positions."""
    exchange = setup_exchange_with_df
    instrument = "BTCUSD"
    amount = Decimal("5")
    limit_price = Decimal("10100.0")
    stop_price = Decimal("9900.0")
    tp_price = Decimal("10500.0")
    sl_price = Decimal("9800.0")

    # Test LIMIT BUY
    position_limit_buy = exchange.open_position(
        instrument,
        Side.BID,
        OrderType.LIMIT,
        amount,
        limit_price=limit_price,
        tp_price=tp_price,
        sl_price=sl_price,
    )
    assert isinstance(position_limit_buy, Position)
    assert position_limit_buy.order_type == OrderType.LIMIT
    assert position_limit_buy.limit_price == limit_price
    assert position_limit_buy.tp_price == tp_price
    assert position_limit_buy.sl_price == sl_price
    assert (
        position_limit_buy.status == PositionStatus.PENDING
    )  # Limit orders are pending

    position_stop_sell = exchange.open_position(
        instrument,
        Side.ASK,
        OrderType.STOP,
        amount,
        stop_price=stop_price,
        tp_price=tp_price,
        sl_price=sl_price,
    )
    assert isinstance(position_stop_sell, Position)
    assert position_stop_sell.order_type == OrderType.STOP
    assert position_stop_sell.stop_price == stop_price
    assert position_stop_sell.tp_price == tp_price
    assert position_stop_sell.sl_price == sl_price
    assert (
        position_stop_sell.status == PositionStatus.PENDING
    )  # Stop orders are pending


def test_backtest_futures_exchange_modify_position(setup_exchange_with_df):
    """Test modifying an existing position's parameters."""
    exchange = setup_exchange_with_df

    # Original position details
    original_pos = Position(
        id="test-id",
        instrument="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        starting_amount=Decimal("10"),
        limit_price=Decimal("10100.0"),
        tp_price=Decimal("10200.0"),
        sl_price=Decimal("9800.0"),
        status=PositionStatus.PENDING,
    )

    # New parameters
    new_tp = Decimal("10250.0")
    new_sl = Decimal("9750.0")
    new_limit = Decimal("10120.0")

    # Call modify_position
    success, updated_pos = exchange.modify_position(
        original_pos, tp_price=new_tp, sl_price=new_sl, limit_price=new_limit
    )

    assert success is True
    assert isinstance(updated_pos, Position)
    assert updated_pos.id == original_pos.id  # ID should remain the same
    assert updated_pos.tp_price == new_tp
    assert updated_pos.sl_price == new_sl
    assert updated_pos.limit_price == new_limit
    # Other fields should remain unchanged
    assert updated_pos.instrument == original_pos.instrument
    assert updated_pos.starting_amount == original_pos.starting_amount


def test_backtest_futures_exchange_modify_position_with_sentinel(
    setup_exchange_with_df,
):
    """Test modifying position where some parameters are left as MODIFY_SENTINEL."""
    # Note: The implementation of exchange.modify_position checks `if arg is not None`.
    # It does not explicitly check for `MODIFY_SENTINEL`. So, if MODIFY_SENTINEL is passed,
    # it will be treated as a valid new value unless it's None.
    # This test checks the behavior based on current implementation logic.
    exchange = setup_exchange_with_df

    original_pos = Position(
        id="test-id-sentinel",
        instrument="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        starting_amount=Decimal("10"),
        limit_price=Decimal("10100.0"),
        tp_price=Decimal("10200.0"),
        sl_price=Decimal("9800.0"),
        status=PositionStatus.PENDING,
    )

    # Modify only SL, pass original values or None for others if not changing.
    # The method signature is `limit_price: Decimal | None = MODIFY_SENTINEL`
    # This means `MODIFY_SENTINEL` is the default if nothing is passed.
    # If we pass `None`, it should retain the old value.
    # If we pass `MODIFY_SENTINEL`, it *should* be updated if the method logic handles it as a value.
    # The current logic is `limit_price if limit_price is not None else position.limit_price`.
    # This means `MODIFY_SENTINEL` itself would be assigned if it's not `None`.

    new_sl = Decimal("9700.0")
    # Test passing explicit value for SL, and None for TP (should keep old TP)
    success, updated_pos = exchange.modify_position(
        original_pos,
        sl_price=new_sl,
        tp_price=None,  # Explicitly pass None to keep old value
    )

    assert success is True
    assert updated_pos.sl_price == new_sl
    assert (
        updated_pos.tp_price == original_pos.tp_price
    )  # Should remain unchanged because None was passed


def test_backtest_futures_exchange_close_position(setup_exchange_with_df):
    """Test closing a position. Verifies return values."""
    exchange = setup_exchange_with_df

    # Create a dummy position to pass to the method
    pos_to_close = Position(
        id="close-me-id",
        instrument="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10"),
        current_amount=Decimal("5"),
        price=Decimal("10000.0"),
        status=PositionStatus.OPEN,
    )
    price = Decimal("10100.0")
    amount_to_close = Decimal("3")

    success, returned_pos = exchange.close_position(
        pos_to_close, price, amount_to_close
    )

    assert success is True
    # The exchange.close_position method returns (True, SENITNEL_POSITION) in the original code.
    # We assert this specific return value.
    assert returned_pos == SENTINEL_POSITION


def test_backtest_futures_exchange_close_all_positions(setup_exchange_with_df):
    """Test close_all_positions method (verifies it runs without error)."""
    exchange = setup_exchange_with_df
    # The method in BacktestFuturesExchange is a no-op, simply returns.
    exchange.close_all_positions()
    # Assert that it executes without raising exceptions.
    assert True


def test_backtest_futures_exchange_cancel_position(setup_exchange_with_df):
    """Test cancel_position method (verifies it runs and returns True)."""
    exchange = setup_exchange_with_df
    position_id_to_cancel = "some-pending-order-id"
    # The method in BacktestFuturesExchange simply returns True.
    success = exchange.cancel_position(position_id_to_cancel)
    assert success is True


def test_backtest_futures_exchange_cancel_all_positions(setup_exchange_with_df):
    """Test cancel_all_positions method (verifies it runs without error)."""
    exchange = setup_exchange_with_df
    # The method in BacktestFuturesExchange is a no-op, simply returns.
    exchange.cancel_all_positions()
    # Assert that it executes without raising exceptions.
    assert True


def test_backtest_futures_exchange_last_tick_property(
    setup_exchange_with_df, sample_df: pd.DataFrame
):
    """Test the last_tick property after subscribing."""
    exchange = setup_exchange_with_df
    instrument = "BTCUSD"
    ticks = list(exchange.subscribe(instrument))

    assert exchange.last_tick is not None
    assert exchange.last_tick.last == pytest.approx(ticks[-1].last)
    assert exchange.last_tick.time == ticks[-1].time

    # Test with df_path as well
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmpfile:
        sample_df.to_csv(tmpfile.name)
        df_path = tmpfile.name

    exchange_path = BacktestFuturesExchange(login_creds={}, df_path=df_path)
    ticks_path = list(exchange_path.subscribe(instrument))

    assert exchange_path.last_tick is not None
    assert exchange_path.last_tick.last == pytest.approx(ticks_path[-1].last)
    assert exchange_path.last_tick.time == ticks_path[-1].time

    os.remove(df_path)  # Clean up
