import pytest
import pandas as pd
from decimal import Decimal
from datetime import datetime

from src.lib.strategy import Strategy
from src.lib.typing import Tick, Position
from src.core.enums import OrderType, PositionStatus, Side, StrategyType
from src.lib.enums import TradingPlatform
from src.lib.exchanges.backtest_futures_exchange import (
    SENTINEL_POSITION as LIBRARY_SENITNEL_POSITION,
)

SENITNEL_POSITION = LIBRARY_SENITNEL_POSITION


# --- Mock Strategy for Integration Tests ---
class MockStrategy(Strategy):
    """
    A flexible mock strategy for testing Backtest integration.
    Can be configured to open/close orders, set TP/SL, etc.
    """

    def __init__(
        self,
        platform: TradingPlatform,
        instrument: str,
        pip_size: float = 0.0001,
        open_order: bool = False,
        close_order: bool = False,
        order_details: dict | None = None,
        tp_sl_on_entry: bool = False,
    ):
        super().__init__(StrategyType.LONG, platform, instrument, pip_size)
        self.open_order = open_order
        self.close_order = close_order
        self.order_details = order_details if order_details else {}
        self.tp_sl_on_entry = (
            tp_sl_on_entry  # Flag to set TP/SL on entry using defaults
        )
        self.last_tick: Tick | None = None
        self._trade_id: str | None = None
        self._initial_run_done: bool = False
        self._closed_trade_id: str | None = None

    def run(self, tick: Tick):
        self.last_tick = tick
        # Logic to open a trade on the first opportunity if configured
        if self.open_order and not self._trade_id and not self._initial_run_done:
            amount = self.order_details.get("amount", Decimal("10"))
            side = self.order_details.get("side", Side.BUY)
            order_type = self.order_details.get("order_type", OrderType.MARKET)

            entry_price = tick.last
            tp_price = None
            sl_price = None

            # Set default TP/SL if tp_sl_on_entry is True
            if self.tp_sl_on_entry:
                if side == Side.BUY:
                    tp_price = Decimal(str(entry_price)) * Decimal("1.02")
                    sl_price = Decimal(str(entry_price)) * Decimal("0.98")
                else:  # SELL
                    tp_price = Decimal(str(entry_price)) * Decimal("0.98")
                    sl_price = Decimal(str(entry_price)) * Decimal("1.02")

            # Use provided TP/SL from order_details if they exist and tp_sl_on_entry is False
            if not self.tp_sl_on_entry:
                tp_price = self.order_details.get("tp_price")
                sl_price = self.order_details.get("sl_price")

            self._trade_id = self._om.open_position(
                self._instrument,
                side,
                order_type,
                amount,
                price=entry_price if order_type == OrderType.MARKET else None,
                limit_price=self.order_details.get("limit_price"),
                stop_price=self.order_details.get("stop_price"),
                tp_price=tp_price,
                sl_price=sl_price,
            )
            if self._trade_id:
                # print(f"Strategy: Opened trade {self._trade_id} for {side.name} {amount} {self._instrument} at {entry_price}")
                pass
            self._initial_run_done = True  # Ensure only one trade is opened per strategy instance in this simple mock

        # Logic to close an open trade if configured
        elif (
            self.close_order
            and self._trade_id
            and self._trade_id in self._om._positions
        ):
            current_pos = self._om._positions[self._trade_id]
            if current_pos.current_amount > 0:
                # Close the full remaining amount of the position
                self._om.close_position(
                    self._trade_id, tick.last, current_pos.current_amount
                )
                # print(f"Strategy: Closed trade {self._trade_id} at {tick.last}")
                self._closed_trade_id = self._trade_id
                self._trade_id = None  # Reset trade ID to indicate no active trade managed by strategy

    def startup(self):
        """Called before backtest starts processing ticks."""
        super().startup()
        # print(f"Strategy startup: {self._instrument}")

    def shutdown(self):
        """Called after backtest finishes processing ticks."""
        # print(f"Strategy shutdown: {self._instrument}")
        # Close any remaining open position if the strategy is configured to do so
        if self._trade_id and self._trade_id in self._om._positions:
            current_pos = self._om._positions[self._trade_id]
            if current_pos.current_amount > 0:
                # Use the last tick seen to close, or a default price if no ticks were processed
                close_price = (
                    Decimal(str(self.last_tick.last))
                    if self.last_tick
                    else Decimal("100.0")
                )
                self._om.close_position(
                    self._trade_id, close_price, current_pos.current_amount
                )
                # print(f"Strategy shutdown: Closed remaining trade {self._trade_id}")
                self._closed_trade_id = self._trade_id
                self._trade_id = None


# --- Sample Data ---
@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Provides a sample DataFrame for backtesting."""
    data = {
        "open": [
            100.0,
            101.0,
            102.0,
            101.5,
            102.5,
            103.0,
            102.8,
            103.5,
            104.0,
            103.5,
            103.8,
            104.2,
            104.5,
            105.0,
            104.8,
        ],
        "high": [
            101.5,
            102.5,
            103.0,
            102.0,
            103.5,
            103.5,
            103.5,
            104.2,
            104.5,
            104.0,
            104.5,
            104.8,
            105.0,
            105.5,
            105.2,
        ],
        "low": [
            99.5,
            100.5,
            101.5,
            101.0,
            102.0,
            102.5,
            102.5,
            103.2,
            103.8,
            103.0,
            103.5,
            104.0,
            104.2,
            104.5,
            104.2,
        ],
        "close": [
            101.0,
            102.0,
            101.5,
            102.5,
            103.0,
            103.2,
            103.2,
            104.0,
            103.8,
            103.9,
            104.3,
            104.6,
            104.9,
            105.2,
            105.0,
        ],
    }
    index = pd.to_datetime(
        [
            "2023-01-01 00:00:00",
            "2023-01-01 00:01:00",
            "2023-01-01 00:02:00",
            "2023-01-01 00:03:00",
            "2023-01-01 00:04:00",
            "2023-01-01 00:05:00",
            "2023-01-01 00:06:00",
            "2023-01-01 00:07:00",
            "2023-01-01 00:08:00",
            "2023-01-01 00:09:00",
            "2023-01-01 00:10:00",
            "2023-01-01 00:11:00",
            "2023-01-01 00:12:00",
            "2023-01-01 00:13:00",
            "2023-01-01 00:14:00",
        ]
    )
    df = pd.DataFrame(data, index=index)
    df.index.name = "timestamp"
    return df


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Provides an empty DataFrame."""
    return pd.DataFrame(
        columns=["open", "high", "low", "close"], index=pd.to_datetime([])
    )


@pytest.fixture
def mock_strategy_factory():
    """
    Factory pattern to create MockStrategy instances with different configurations.
    This is useful for integration tests where Backtest uses a concrete strategy.
    """

    def create_strategy(
        platform: TradingPlatform,
        instrument: str,
        open_order: bool = False,
        close_order: bool = False,
        order_details: dict | None = None,
        tp_sl_on_entry: bool = False,
        pip_size: float = 0.0001,
    ) -> MockStrategy:
        return MockStrategy(
            platform=platform,
            instrument=instrument,
            open_order=open_order,
            close_order=close_order,
            order_details=order_details,
            tp_sl_on_entry=tp_sl_on_entry,
            pip_size=pip_size,
        )

    return create_strategy


# --- Mock Position creation helper ---
def create_position_for_test(
    id: str,
    side: Side,
    amount: Decimal,
    price: float | None,
    realised_pnl: Decimal = Decimal("0.0"),
    unrealised_pnl: Decimal = Decimal("0.0"),
    status: PositionStatus = PositionStatus.CLOSED,
    order_type: OrderType = OrderType.MARKET,
) -> Position:
    """Helper to create Position objects for testing."""
    return Position(
        id=id,
        instrument="test",
        side=side,
        order_type=order_type,
        starting_amount=amount,
        current_amount=Decimal("0.0") if status == PositionStatus.CLOSED else amount,
        price=price,
        status=status,
        realised_pnl=realised_pnl,
        unrealised_pnl=unrealised_pnl,
        created_at=datetime.now(),  # Set a dummy creation time
        closed_at=datetime.now() if status == PositionStatus.CLOSED else None,
    )


# --- Mock Order Manager State Helper ---
from unittest.mock import Mock
from lib.order_managers.backtest_futures_order_manager import (
    BacktestFuturesOrderManager,
)


def simulate_om_state(
    closed_positions: list[Position] | None = None,
    open_positions: list[Position] | None = None,
    balance: Decimal = Decimal("100000.0"),
    margin: Decimal = Decimal("0.0"),
    equity: Decimal = Decimal("0.0"),
    free_margin: Decimal = Decimal("100000.0"),
) -> Mock:
    """
    Helper to create a mock BacktestFuturesOrderManager with specific internal state.
    """
    mock_om = Mock(spec=BacktestFuturesOrderManager)
    mock_om._closed_positions = closed_positions if closed_positions is not None else []

    # _positions is a dict mapping id to Position object
    mock_om._positions = {
        p.id: p for p in (open_positions if open_positions is not None else [])
    }

    mock_om._balance = balance
    mock_om._margin = margin
    mock_om._equity = equity
    mock_om._free_margin = free_margin

    # Provide .positions property that returns an iterable of position values
    mock_om.positions = mock_om._positions.values()

    # Mock other attributes/methods that Backtest might access if necessary
    mock_om._exchange = Mock()  # Assign a dummy exchange object
    mock_om._exchange.last_tick = None  # Default last_tick

    return mock_om
