from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.core.enums import Side, OrderType, PositionStatus
from src.trading_lib.order_managers.backtest_futures_order_manager import (
    BacktestFuturesOrderManager,
)
from src.trading_lib.typing import Position, Tick


@pytest.fixture
def mock_exchange():
    """Provides a mock exchange object."""
    exchange = MagicMock()
    type(exchange).last_tick = PropertyMock(
        return_value=Tick(last=100.0, time=MagicMock())
    )
    return exchange


@pytest.fixture
def backtest_order_manager(mock_exchange):
    """Provides a BacktestFuturesOrderManager instance with a mock exchange."""
    om = BacktestFuturesOrderManager(starting_balance=10000, leverage=10)
    om._exchange = mock_exchange
    return om


def test_initialization():
    """Tests correct initialization of the order manager."""
    om = BacktestFuturesOrderManager(starting_balance=5000, leverage=20)
    assert om._balance == Decimal("5000")
    assert om._leverage == 20
    assert om._free_margin == Decimal("5000")


def test_open_position_failure_insufficient_margin(
    backtest_order_manager, mock_exchange
):
    """Tests failing to open a position due to insufficient margin."""
    pos_id = backtest_order_manager.open_position(
        "EURUSD", Side.BID, OrderType.MARKET, Decimal("1001")
    )  # 1001 * 10 > 10000

    assert pos_id is None
    mock_exchange.open_position.assert_not_called()
    assert len(backtest_order_manager._positions) == 0
    assert backtest_order_manager._margin == 0


def test_close_full_position(backtest_order_manager):
    """Tests closing a full position and checks accounting."""
    pos = Position(
        id="p1",
        instrument="ANY",
        side=Side.BID,
        price=100,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("50"),
    )
    backtest_order_manager._positions["p1"] = pos
    backtest_order_manager._margin = Decimal("50")

    # Simulate a $200 profit
    with patch.object(backtest_order_manager, "_calc_upl", return_value=Decimal("200")):
        type(backtest_order_manager._exchange).last_tick = PropertyMock(
            return_value=Tick(last=104.0, time=MagicMock())
        )

        success = backtest_order_manager.close_position("p1", Decimal("50"))

        assert success is True
        assert "p1" not in backtest_order_manager._positions
        assert len(backtest_order_manager._closed_positions) == 1
        closed_pos = backtest_order_manager._closed_positions[0]

        assert closed_pos.status.value == PositionStatus.CLOSED.value
        assert closed_pos.close_price == 104.0
        assert closed_pos.realised_pnl == Decimal("200")
        assert backtest_order_manager._balance == Decimal("10200")  # 10000 + 200 profit
        assert backtest_order_manager._margin == 0  # Margin is released


def test_close_partial_position(backtest_order_manager):
    """Tests closing part of a position and checks accounting."""
    pos = Position(
        id="p1",
        instrument="ANY",
        side=Side.BID,
        price=100,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("100"),
    )
    backtest_order_manager._positions["p1"] = pos
    backtest_order_manager._margin = Decimal("100")

    with patch.object(
        backtest_order_manager, "_calc_upl", return_value=Decimal("200")
    ): 
        type(backtest_order_manager._exchange).last_tick = PropertyMock(
            return_value=Tick(last=105.0, time=MagicMock())
        )

        success = backtest_order_manager.close_position("p1", Decimal("40"))

        assert success is True
        assert "p1" in backtest_order_manager._positions

        remaining_pos = backtest_order_manager._positions["p1"]
        assert remaining_pos.current_amount == Decimal("60")
        assert remaining_pos.realised_pnl == Decimal("200")

        assert backtest_order_manager._balance == Decimal(
            "10200"
        )  # Realised the $200 profit
        assert backtest_order_manager._margin == Decimal("60")  # Margin reduced

@patch("src.lib.order_managers.backtest_futures_order_manager.PositionStatus", PositionStatus)
def test_cancel_position(backtest_order_manager):
    """Tests cancelling a pending order."""
    pending_pos = Position(
        id="p1",
        instrument="ANY",
        side=Side.BID,
        order_type=OrderType.LIMIT,
        status=PositionStatus.PENDING,
        starting_amount=Decimal("50"),
    )
    open_pos = Position(
        id="p2",
        instrument="ANY",
        side=Side.BID,
        order_type=OrderType.MARKET,
        status=PositionStatus.OPEN,
        starting_amount=Decimal("50"),
    )
    backtest_order_manager._positions = {"p1": pending_pos, "p2": open_pos}
    backtest_order_manager._margin = Decimal("100")

    assert (
        backtest_order_manager.cancel_position("p2") is False
    )  # Cannot cancel open pos
    assert backtest_order_manager.cancel_position("p1") is True

    assert "p1" not in backtest_order_manager._positions
    assert pending_pos.status == PositionStatus.CANCELLED
    assert backtest_order_manager._margin == Decimal(
        "50"
    )  # Margin for cancelled pos is released