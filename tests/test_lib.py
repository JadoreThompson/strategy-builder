import pytest
import pandas as pd
from datetime import datetime

from unittest.mock import MagicMock, patch

from src.lib.order_managers import DemoFuturesOrderManager
from src.core.enums import PositionStatus, Side, OrderType
from src.lib.typing import Position, Tick, BacktestResult
from src.lib.backtest import Backtest
from src.lib.strategy import Strategy
from src.lib.enums import TradingPlatform
from src.lib.order_managers.backtest_futures_order_manager import (
    BacktestFuturesOrderManager,
)


# --- DemoFuturesOrderManager Tests ---


@pytest.fixture
def demo_futures_om(monkeypatch):
    monkeypatch.setattr(
        "src.lib.order_managers.demo_futures_order_manager.PositionStatus",
        PositionStatus,
    )
    monkeypatch.setattr(
        "src.lib.order_managers.demo_futures_order_manager.OrderType", OrderType
    )
    return DemoFuturesOrderManager(starting_balance=1000.0)


@pytest.fixture
def demo_futures_om_no_balance():
    return DemoFuturesOrderManager()


def test_demo_futures_om_init(demo_futures_om):
    assert demo_futures_om._balance == 1000.0
    assert not demo_futures_om._positions


def test_demo_futures_om_init_no_balance_warning(caplog):
    DemoFuturesOrderManager()
    assert "No starting balance provided" in caplog.text


def test_demo_futures_om_login_success(demo_futures_om):
    assert demo_futures_om.login() is True


def test_demo_futures_om_login_no_balance_raises_error(demo_futures_om_no_balance):
    with pytest.raises(ValueError, match="Starting balance not provided."):
        demo_futures_om_no_balance.login()


def test_demo_futures_om_open_position_market_buy(demo_futures_om):
    initial_balance = demo_futures_om._balance
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )
    assert pos_id in demo_futures_om._positions
    pos = demo_futures_om._positions[pos_id]
    assert pos.instrument == "XAUUSD"
    assert pos.side == Side.BID
    assert pos.order_type == OrderType.MARKET
    assert pos.current_amount == 10.0
    assert pos.price == 1800.0
    assert demo_futures_om._balance == initial_balance - 10.0


def test_demo_futures_om_open_position_limit_sell(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.LIMIT,
        amount=5.0,
        limit_price=1810.0,
    )
    pos = demo_futures_om._positions[pos_id]
    assert pos.limit_price == 1810.0
    assert (
        pos.status.value == PositionStatus.PENDING.value
    )  # Limit orders are pending initially
    assert demo_futures_om._balance == 1000.0 - 5.0


def test_demo_futures_om_update_position_success(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
        sl_price=1790.0,
    )
    updated = demo_futures_om.update_position(
        position_id=pos_id, tp_price=1820.0, sl_price=1780.0
    )
    assert updated is True
    pos = demo_futures_om._positions[pos_id]
    assert pos.tp_price == 1820.0
    assert pos.sl_price == 1780.0
    assert pos.price == 1800.0  # Other fields remain unchanged


def test_demo_futures_om_update_position_not_found(demo_futures_om):
    updated = demo_futures_om.update_position(
        position_id="non_existent_id", tp_price=1820.0
    )
    assert updated is False


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_demo_futures_om_close_position_full_amount_buy(
    mock_get_datetime, demo_futures_om
):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )
    initial_balance = demo_futures_om._balance

    # Closing at a profit
    closed = demo_futures_om.close_position(
        position_id=pos_id, price=1810.0, amount=10.0
    )
    assert closed is True
    assert pos_id not in demo_futures_om._positions
    assert demo_futures_om._balance == 1090.00


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_demo_futures_om_close_position_full_amount_sell(
    mock_get_datetime, demo_futures_om
):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )
    initial_balance = demo_futures_om._balance  # Balance already deducted by amount

    # Simulate closing at a profit
    closed = demo_futures_om.close_position(
        position_id=pos_id, price=1790.0, amount=10.0
    )
    assert closed is True
    assert pos_id not in demo_futures_om._positions
    assert demo_futures_om._balance == initial_balance


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_demo_futures_om_close_position_partial_amount(
    mock_get_datetime, demo_futures_om
):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )
    initial_balance = demo_futures_om._balance

    closed = demo_futures_om.close_position(
        position_id=pos_id, price=1805.0, amount=5.0
    )
    assert closed is True
    assert pos_id in demo_futures_om._positions
    pos = demo_futures_om._positions[pos_id]
    assert pos.current_amount == 5.0
    assert (
        pos.realised_pnl == 5.0 * (1805.0 - 1800.0) / 1800.0 * 1800.0
    )
    assert (
        pos.unrealised_pnl == 5.0 * (1805.0 - 1800.0) / 1800.0 * 1800.0
    )


def test_demo_futures_om_close_position_not_found(demo_futures_om):
    closed = demo_futures_om.close_position(
        position_id="non_existent_id", price=1800.0, amount=1.0
    )
    assert closed is False


def test_demo_futures_om_close_position_amount_greater_than_open(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )
    closed = demo_futures_om.close_position(
        position_id=pos_id, price=1800.0, amount=15.0
    )
    assert closed is False
    assert pos_id in demo_futures_om._positions  # Position not closed


def test_demo_futures_om_cancel_position_pending_success(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.LIMIT,
        amount=10.0,
        limit_price=1795.0,
    )
    assert pos_id in demo_futures_om._positions
    assert (
        demo_futures_om._positions[pos_id].status.value == PositionStatus.PENDING.value
    )

    cancelled = demo_futures_om.cancel_position(pos_id)
    assert cancelled is True
    assert pos_id not in demo_futures_om._positions


def test_demo_futures_om_cancel_position_not_pending_fail(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )
    assert pos_id in demo_futures_om._positions
    assert (
        demo_futures_om._positions[pos_id].status.value != PositionStatus.PENDING.value
    )

    cancelled = demo_futures_om.cancel_position(pos_id)
    assert (
        cancelled is None
    )  # The method returns None if the position is not pending or not found
    assert pos_id in demo_futures_om._positions  # Position not cancelled


def test_demo_futures_om_cancel_position_not_found(demo_futures_om):
    cancelled = demo_futures_om.cancel_position("non_existent_id")
    assert cancelled is None


def test_demo_futures_om_cancel_all_positions(demo_futures_om):
    demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.LIMIT,
        amount=10.0,
        limit_price=1795.0,
    )
    demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.LIMIT,
        amount=5.0,
        limit_price=1805.0,
    )
    # A market position should not be cancelled
    market_pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=2.0,
        price=1800.0,
    )

    assert len(demo_futures_om._positions) == 3
    demo_futures_om.cancel_all_positions()
    assert len(demo_futures_om._positions) == 1  # Only the market position remains
    assert market_pos_id in demo_futures_om._positions


# --- BacktestFuturesOrderManager Tests ---


@pytest.fixture
def backtest_futures_om():
    return BacktestFuturesOrderManager(starting_balance=10000.0)


def test_backtest_futures_om_init(backtest_futures_om):
    assert backtest_futures_om._balance == 10000.0
    assert not backtest_futures_om._positions
    assert not backtest_futures_om._closed_positions


def test_backtest_futures_om_login(backtest_futures_om):
    assert backtest_futures_om.login() is True


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_futures_om_close_position_success(
    mock_get_datetime, backtest_futures_om
):
    pos_id = backtest_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )

    initial_balance = backtest_futures_om._balance  # This reflects the amount spent

    # Close at a profit
    closed = backtest_futures_om.close_position(
        position_id=pos_id, price=1810.0, amount=10.0
    )
    assert closed is True
    assert pos_id not in backtest_futures_om._positions
    assert len(backtest_futures_om._closed_positions) == 1

    closed_pos = backtest_futures_om._closed_positions[0]
    assert closed_pos.id == pos_id
    assert closed_pos.status.value == PositionStatus.CLOSED.value
    assert closed_pos.close_price == 1810.0
    assert (
        closed_pos.realised_pnl == 10.0 * (1810.0 - 1800.0) / 1800.0 * 1800.0
    )
    assert backtest_futures_om._balance == initial_balance


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_futures_om_close_position_partial_success(
    mock_get_datetime, backtest_futures_om
):
    pos_id = backtest_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=10.0,
        price=1800.0,
    )

    closed = backtest_futures_om.close_position(
        position_id=pos_id, price=1805.0, amount=5.0
    )
    assert closed is True
    assert pos_id in backtest_futures_om._positions  # Position still open
    assert (
        len(backtest_futures_om._closed_positions) == 0
    )

    pos = backtest_futures_om._positions[pos_id]
    assert pos.current_amount == 5.0
    assert pos.realised_pnl == 5.0 * (1805.0 - 1800.0) / 1800.0 * 1800.0

    # Close remaining
    closed_final = backtest_futures_om.close_position(
        position_id=pos_id, price=1810.0, amount=5.0
    )
    assert closed_final is True
    assert pos_id not in backtest_futures_om._positions
    assert len(backtest_futures_om._closed_positions) == 1

    final_closed_pos = backtest_futures_om._closed_positions[0]
    assert final_closed_pos.id == pos_id
    assert (
        final_closed_pos.realised_pnl
        == (5.0 * (1805.0 - 1800.0) + 5.0 * (1810.0 - 1800.0)) / 1800.0 * 1800.0
    )  # Sum of PNLs


def test_backtest_futures_om_close_position_not_in_active_positions(
    backtest_futures_om,
):
    closed = backtest_futures_om.close_position(
        position_id="non_existent", price=100, amount=1
    )
    assert closed is False
    assert not backtest_futures_om._closed_positions


# --- Backtest Class Tests ---


class MockStrategy(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticks_received = []
        self.open_called = 0
        self.close_called = 0

    def run(self, tick: Tick):
        self.ticks_received.append(tick)
        if len(self.ticks_received) == 2:
            self._om.open_position(
                instrument=self._instrument,
                side=Side.BID,
                order_type=OrderType.MARKET,
                amount=10.0,
                price=tick.last,
            )
        elif len(self.ticks_received) == 4:
            for pos_id, pos in self._om._positions.items():
                self._om.close_position(
                    position_id=pos_id, price=tick.last, amount=pos.starting_amount
                )
                break


@pytest.fixture
def sample_csv_data(tmp_path):
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2023-01-01 09:00:00",
                    "2023-01-01 09:01:00",
                    "2023-01-01 09:02:00",
                    "2023-01-01 09:03:00",
                    "2023-01-01 09:04:00",
                ]
            ),
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5],
        }
    )
    df_path = tmp_path / "test_data.csv"
    df.to_csv(df_path, index=False)
    return str(df_path)


@pytest.fixture
def mock_strategy_factory():
    def _factory(om_mock=None):
        strat = MockStrategy(
            type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
        )
        if om_mock:
            strat._om = om_mock
        return strat

    return _factory


@pytest.fixture()
def patched_bt_result_cls(monkeypatch):
    monkeypatch.setattr("src.lib.backtest.BacktestResult", BacktestResult)


def test_backtest_init(sample_csv_data, mock_strategy_factory):
    strat = mock_strategy_factory()
    starting_balance = 50000.0
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    assert backtest._starting_balance == starting_balance
    assert backtest._strat == strat
    assert isinstance(strat._om, BacktestFuturesOrderManager)
    assert strat._om._balance == starting_balance
    assert backtest._df_path == sample_csv_data


def test_backtest_run_no_trades(sample_csv_data, patched_bt_result_cls):

    class NoTradeStrategy(Strategy):
        def run(self, tick: Tick):
            pass

    strat = NoTradeStrategy(
        type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
    )
    starting_balance = 100_000.0
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    result = backtest.run()

    assert isinstance(result, BacktestResult)
    assert result.total_pnl == 0.0
    assert result.starting_balance == starting_balance
    assert result.end_balance == starting_balance
    assert result.total_trades == 0
    assert result.win_rate == 0.0


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_run_with_trades_profit(
    mock_get_datetime, sample_csv_data, mock_strategy_factory, patched_bt_result_cls
):
    strat = mock_strategy_factory()
    starting_balance = 1000.0
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    result = backtest.run()

    expected_pnl_per_unit = (103.5 - 101.5) / 101.5 * 101.5
    expected_total_pnl = 10.0 * expected_pnl_per_unit

    assert isinstance(result, BacktestResult)
    expected_total_pnl_calculated = 10.0 * (103.5 - 101.5)

    assert result.total_pnl == pytest.approx(expected_total_pnl_calculated)
    assert result.starting_balance == starting_balance
    assert result.end_balance == pytest.approx(
        starting_balance - 10.0
    )  # Balance reflects initial 'amount' deduction
    assert result.total_trades == 1
    assert result.win_rate == 1.0


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_run_with_trades_loss(
    mock_get_datetime, tmp_path, mock_strategy_factory
):
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2023-01-01 09:00:00",
                    "2023-01-01 09:01:00",
                    "2023-01-01 09:02:00",
                    "2023-01-01 09:03:00",
                    "2023-01-01 09:04:00",
                ]
            ),
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [105.0, 104.0, 103.0, 102.0, 101.0],
        }
    )
    df_path = tmp_path / "test_data_loss.csv"
    df.to_csv(df_path, index=False)

    strat = mock_strategy_factory()
    starting_balance = 1000.0
    backtest = Backtest(
        strat=strat, df_path=str(df_path), starting_balance=starting_balance
    )

    result = backtest.run()

    expected_total_pnl_calculated = 10.0 * (102.0 - 104.0)  # Loss of 20.0

    assert result.total_pnl == pytest.approx(expected_total_pnl_calculated)
    assert result.starting_balance == starting_balance
    assert result.end_balance == pytest.approx(starting_balance - 10.0)
    assert result.total_trades == 1
    assert result.win_rate == 0.0  # 0 wins out of 1 trade


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_run_with_open_position_at_end(
    mock_get_datetime, sample_csv_data, mock_strategy_factory
):
    class OpenOnlyStrategy(Strategy):
        def run(self, tick: Tick):
            if len(self._om._positions) == 0:  # Open only one position
                self._om.open_position(
                    instrument=self._instrument,
                    side=Side.BID,
                    order_type=OrderType.MARKET,
                    amount=10.0,
                    price=tick.last,
                )

    strat = OpenOnlyStrategy(
        type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
    )
    starting_balance = 1000.0
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    result = backtest.run()

    assert len(strat._om._positions) == 1
    open_pos = list(strat._om._positions.values())[0]

    assert (
        result.total_pnl == 0.0
    )  # No positions were actually closed, so realized PNL is 0
    assert result.starting_balance == starting_balance
    assert result.end_balance == pytest.approx(
        starting_balance - 10.0
    )  # Balance reflects initial 'amount' deduction
    assert result.total_trades == 1  # One position was opened, even if not closed
    assert result.win_rate == 0.0


def test_backtest_chunking(tmp_path, mock_strategy_factory):
    num_rows = 2500
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(
                pd.date_range("2023-01-01", periods=num_rows, freq="min")
            ),
            "open": range(100, 100 + num_rows),
            "high": range(101, 101 + num_rows),
            "low": range(99, 99 + num_rows),
            "close": [i + 0.5 for i in range(100, 100 + num_rows)],
        }
    )
    df_path = tmp_path / "large_data.csv"
    df.to_csv(df_path, index=False)

    strat = mock_strategy_factory()
    backtest = Backtest(strat=strat, df_path=str(df_path))

    result = backtest.run()

    assert len(strat.ticks_received) == num_rows  
    assert result.total_trades == 1
    assert len(strat._om._closed_positions) == 1
