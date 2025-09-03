from decimal import Decimal
from pprint import pprint
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
    monkeypatch.setattr("src.lib.order_managers.demo_futures_order_manager.Side", Side)
    return DemoFuturesOrderManager(starting_balance=Decimal("1000.0"))


@pytest.fixture
def demo_futures_om_no_balance():
    return DemoFuturesOrderManager()


# --- DemoFuturesOrderManager Tests ---


def test_demo_futures_om_init(demo_futures_om):
    assert demo_futures_om._balance == Decimal("1000.0")
    assert not demo_futures_om._positions


def test_demo_futures_om_login_success(demo_futures_om):
    assert demo_futures_om.login() is True


def test_demo_futures_om_open_position_market_buy(demo_futures_om):
    initial_balance = demo_futures_om._balance
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    assert pos_id in demo_futures_om._positions
    pos = demo_futures_om._positions[pos_id]
    assert pos.instrument == "XAUUSD"
    assert pos.side == Side.BID
    assert pos.order_type == OrderType.MARKET
    assert pos.current_amount == Decimal("10.0")
    assert pos.price == Decimal("1800.0")
    assert demo_futures_om._balance == initial_balance
    assert demo_futures_om._margin == pos.current_amount
    assert demo_futures_om._free_margin == initial_balance - pos.current_amount


def test_demo_futures_om_open_position_limit_sell(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.LIMIT,
        amount=Decimal("5.0"),
        limit_price=Decimal("1810.0"),
    )
    pos = demo_futures_om._positions[pos_id]
    assert pos.limit_price == Decimal("1810.0")
    assert (
        pos.status.value == PositionStatus.PENDING.value
    )  # Limit orders are pending initially
    assert demo_futures_om._balance == Decimal("1000.0")


def test_demo_futures_om_open_position_insufficient_margin(demo_futures_om):
    """
    Test opening a position when there isn't enough free margin.
    """
    demo_futures_om._free_margin = Decimal("50.0")
    initial_balance = demo_futures_om._balance
    initial_margin = demo_futures_om._margin
    initial_free_margin = demo_futures_om._free_margin

    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    assert pos_id is None  # Position should not be opened
    assert len(demo_futures_om._positions) == 0
    assert demo_futures_om._balance == initial_balance
    assert demo_futures_om._margin == initial_margin
    assert demo_futures_om._free_margin == initial_free_margin


def test_demo_futures_om_update_position_success(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
        sl_price=Decimal("1790.0"),
    )
    updated = demo_futures_om.update_position(
        position_id=pos_id, tp_price=Decimal("1820.0"), sl_price=Decimal("1780.0")
    )
    assert updated is True
    pos = demo_futures_om._positions[pos_id]
    assert pos.tp_price == Decimal("1820.0")
    assert pos.sl_price == Decimal("1780.0")
    assert pos.price == Decimal("1800.0")  # Other fields remain unchanged


def test_demo_futures_om_update_position_not_found(demo_futures_om):
    updated = demo_futures_om.update_position(
        position_id="non_existent_id", tp_price=Decimal("1820.0")
    )
    assert updated is False


def test_demo_futures_om_update_position_with_sl_tp_changes(demo_futures_om):
    """
    Test updating a position with new SL and TP prices.
    """
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
        sl_price=Decimal("1790.0"),
        tp_price=Decimal("1810.0"),
    )
    assert pos_id is not None
    initial_pos = demo_futures_om._positions[pos_id]
    assert initial_pos.sl_price == Decimal("1790.0")
    assert initial_pos.tp_price == Decimal("1810.0")

    updated = demo_futures_om.update_position(
        position_id=pos_id, sl_price=Decimal("1785.0"), tp_price=Decimal("1815.0")
    )
    assert updated is True
    updated_pos = demo_futures_om._positions[pos_id]
    assert updated_pos.sl_price == Decimal("1785.0")
    assert updated_pos.tp_price == Decimal("1815.0")
    assert updated_pos.price == Decimal(
        "1800.0"
    )  # Ensure other attributes are preserved


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
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    # Closing at a profit
    pos = demo_futures_om._positions[pos_id]
    closed = demo_futures_om.close_position(
        position_id=pos_id, price=Decimal("1810.0"), amount=Decimal("10.0")
    )
    assert closed is True
    assert pos_id not in demo_futures_om._positions
    assert (
        demo_futures_om._balance
        == demo_futures_om._balance
        + (Decimal("1810.0") / pos.price)
        * pos.current_amount
        * demo_futures_om._leverage
    )


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
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    pos = demo_futures_om._positions[pos_id]

    # Simulate closing at a profit
    closed = demo_futures_om.close_position(
        position_id=pos_id, price=Decimal("1790.0"), amount=Decimal("10.0")
    )
    assert closed is True
    assert pos_id not in demo_futures_om._positions
    assert (
        demo_futures_om._balance
        == demo_futures_om._balance
        + (pos.price / Decimal("1790.0"))
        * pos.current_amount
        * demo_futures_om._leverage
    )


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
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    closed = demo_futures_om.close_position(
        position_id=pos_id, price=Decimal("1805.0"), amount=Decimal("5.0")
    )
    assert closed is True
    assert pos_id in demo_futures_om._positions

    pos = demo_futures_om._positions[pos_id]
    assert pos.current_amount == Decimal("5.0")

    k = Decimal("5.0") * demo_futures_om._leverage
    pnl = (Decimal("1805.0") - Decimal("1800.0")) / Decimal("1800.0") * k
    assert pos.realised_pnl == pytest.approx(pnl)
    assert pos.unrealised_pnl == pytest.approx(pnl)


def test_demo_futures_om_close_position_not_found(demo_futures_om):
    closed = demo_futures_om.close_position(
        position_id="non_existent_id", price=Decimal("1800.0"), amount=Decimal("1.0")
    )
    assert closed is False


def test_demo_futures_om_close_position_amount_greater_than_open(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    closed = demo_futures_om.close_position(
        position_id=pos_id, price=Decimal("1800.0"), amount=Decimal("15.0")
    )
    assert closed is False
    assert pos_id in demo_futures_om._positions  # Position not closed


def test_demo_futures_om_cancel_position_pending_success(demo_futures_om):
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.LIMIT,
        amount=Decimal("10.0"),
        limit_price=Decimal("1795.0"),
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
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    assert pos_id in demo_futures_om._positions
    assert (
        demo_futures_om._positions[pos_id].status.value != PositionStatus.PENDING.value
    )

    cancelled = demo_futures_om.cancel_position(pos_id)
    assert cancelled is False
    assert pos_id in demo_futures_om._positions  # Position not cancelled


def test_demo_futures_om_cancel_position_not_found(demo_futures_om):
    cancelled = demo_futures_om.cancel_position("non_existent_id")
    assert cancelled is False


def test_demo_futures_om_cancel_all_positions(demo_futures_om):
    demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.LIMIT,
        amount=Decimal("10.0"),
        limit_price=Decimal("1795.0"),
    )
    demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.LIMIT,
        amount=Decimal("5.0"),
        limit_price=Decimal("1805.0"),
    )
    # A market position should not be cancelled
    market_pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("2.0"),
        price=Decimal("1800.0"),
    )

    assert len(demo_futures_om._positions) == 3
    demo_futures_om.cancel_all_positions()
    assert len(demo_futures_om._positions) == 1  # Only the market position remains
    assert market_pos_id in demo_futures_om._positions


def test_demo_futures_om_perform_risk_checks_margin_call(demo_futures_om):
    """
    Test the margin call functionality when free margin drops to zero or below.
    """
    demo_futures_om = DemoFuturesOrderManager(
        starting_balance=Decimal("200.0"), leverage=10
    )
    pos_id = demo_futures_om.open_position(
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        amount=Decimal("1.0"),
        price=Decimal("1800.0"),
    )
    assert pos_id is not None
    assert demo_futures_om._free_margin == Decimal("200.0") - Decimal("1.0")
    with patch.object(
        demo_futures_om, "_calc_upl", return_value=Decimal("-50.0")
    ) as mock_calc_upl:
        tick = Tick(
            last=Decimal("1790.0"), time=datetime.now()
        )  # The actual tick price doesn't matter for this mocked test
        closed_successfully = demo_futures_om.perform_risk_checks(tick)

        assert closed_successfully is True
        assert len(demo_futures_om._positions) == 1


def test_demo_futures_om_calc_upl_bid_profit(demo_futures_om):
    """Test PNL calculation for a BID position with profit."""
    demo_futures_om = DemoFuturesOrderManager(leverage=10)
    pos = Position(
        id="1",
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    close_price = Decimal("1810.0")
    expected_pnl = (close_price / pos.price) * (
        pos.starting_amount * demo_futures_om._leverage
    ) - (pos.starting_amount * demo_futures_om._leverage)
    assert demo_futures_om._calc_upl(
        pos, close_price, pos.starting_amount
    ) == pytest.approx(expected_pnl)


def test_demo_futures_om_calc_upl_bid_loss(demo_futures_om):
    """Test PNL calculation for a BID position with loss."""
    demo_futures_om = DemoFuturesOrderManager(leverage=10)
    pos = Position(
        id="1",
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    close_price = Decimal("1790.0")
    expected_pnl = (close_price / pos.price) * (
        pos.starting_amount * demo_futures_om._leverage
    ) - (pos.starting_amount * demo_futures_om._leverage)
    assert demo_futures_om._calc_upl(
        pos, close_price, pos.starting_amount
    ) == pytest.approx(expected_pnl)


def test_demo_futures_om_calc_upl_ask_profit(demo_futures_om):
    """Test PNL calculation for an ASK position with profit."""
    demo_futures_om = DemoFuturesOrderManager(leverage=10)
    pos = Position(
        id="1",
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    close_price = Decimal("1790.0")
    total_value = Decimal(str(pos.starting_amount * demo_futures_om._leverage))
    expected_pnl = Decimal(str((pos.price - close_price) / pos.price * total_value))

    assert demo_futures_om._calc_upl(
        pos, close_price, pos.starting_amount
    ) == pytest.approx(expected_pnl)


def test_demo_futures_om_calc_upl_ask_loss(demo_futures_om):
    """Test PNL calculation for an ASK position with loss."""
    demo_futures_om = DemoFuturesOrderManager(leverage=10)
    pos = Position(
        id="1",
        instrument="XAUUSD",
        side=Side.ASK,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    close_price = Decimal("1810.0")

    expected_pnl = Decimal(
        (pos.price - close_price)
        / pos.price
        * pos.starting_amount
        * demo_futures_om._leverage
    )

    assert demo_futures_om._calc_upl(
        pos, close_price, pos.starting_amount
    ) == pytest.approx(expected_pnl)


def test_demo_futures_om_calc_upl_zero_division(demo_futures_om):
    """Test PNL calculation when close price is zero."""
    demo_futures_om = DemoFuturesOrderManager(leverage=10)
    pos = Position(
        id="1",
        instrument="XAUUSD",
        side=Side.BID,
        order_type=OrderType.MARKET,
        starting_amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )
    close_price = Decimal("0.0")

    assert demo_futures_om._calc_upl(pos, close_price, pos.starting_amount) == Decimal(
        "-100.0"
    )


# --- BacktestFuturesOrderManager Tests ---


@pytest.fixture
def backtest_futures_om(monkeypatch):
    return BacktestFuturesOrderManager(starting_balance=Decimal("10000.0"))


def test_backtest_futures_om_init(backtest_futures_om):
    assert backtest_futures_om._balance == Decimal("10000.0")
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
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    initial_balance = backtest_futures_om._balance

    # Close at a profit
    closed = backtest_futures_om.close_position(
        position_id=pos_id, price=Decimal("1810.0"), amount=Decimal("10.0")
    )
    assert closed is True
    assert pos_id not in backtest_futures_om._positions
    assert len(backtest_futures_om._closed_positions) == 1

    closed_pos = backtest_futures_om._closed_positions[0]
    assert closed_pos.id == pos_id
    assert closed_pos.status.value == PositionStatus.CLOSED.value
    assert closed_pos.close_price == Decimal("1810.0")
    k = backtest_futures_om._leverage * Decimal("10.0")
    assert closed_pos.realised_pnl == pytest.approx(
        k * (Decimal("1810.0") - Decimal("1800.0")) / Decimal("1800.0")
    )
    assert backtest_futures_om._balance == initial_balance + (
        k * (Decimal("1810.0") - Decimal("1800.0")) / Decimal("1800.0")
    )


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
        amount=Decimal("10.0"),
        price=Decimal("1800.0"),
    )

    closed = backtest_futures_om.close_position(
        position_id=pos_id, price=Decimal("1805.0"), amount=Decimal("5.0")
    )
    assert closed is True
    assert pos_id in backtest_futures_om._positions  # Position still open
    assert len(backtest_futures_om._closed_positions) == 0

    pos = backtest_futures_om._positions[pos_id]
    assert pos.current_amount == Decimal("5.0")

    k = backtest_futures_om._leverage * Decimal("5.0")
    assert pos.realised_pnl == pytest.approx(
        k * (Decimal("1805.0") - Decimal("1800.0")) / Decimal("1800.0")
    )

    # Close remaining
    closed_final = backtest_futures_om.close_position(
        position_id=pos_id, price=Decimal("1810.0"), amount=Decimal("5.0")
    )
    assert closed_final is True
    assert pos_id not in backtest_futures_om._positions
    assert len(backtest_futures_om._closed_positions) == 1

    final_closed_pos = backtest_futures_om._closed_positions[0]
    assert final_closed_pos.id == pos_id
    k = backtest_futures_om._leverage * Decimal("5.0")
    assert final_closed_pos.realised_pnl == pytest.approx(
        k * (Decimal("1810.0") - Decimal("1800.0")) / Decimal("1800.0")
        + k * (Decimal("1805.0") - Decimal("1800.0")) / Decimal("1800.0")
    )


def test_backtest_futures_om_close_position_not_in_active_positions(
    backtest_futures_om,
):
    closed = backtest_futures_om.close_position(
        position_id="non_existent", price=Decimal("100"), amount=Decimal("1.0")
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
                amount=Decimal("10.0"),
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
            "open": [
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
            ],
            "high": [
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
                Decimal("105"),
            ],
            "low": [
                Decimal("99"),
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
            ],
            "close": [
                Decimal("100.5"),
                Decimal("101.5"),
                Decimal("102.5"),
                Decimal("103.5"),
                Decimal("104.5"),
            ],
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
    starting_balance = Decimal("50000.0")
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
    starting_balance = Decimal("100000.0")
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    result = backtest.run()

    assert isinstance(result, BacktestResult)
    assert result.total_pnl == Decimal("0.0")
    assert result.starting_balance == starting_balance
    assert result.end_balance == starting_balance
    assert result.total_trades == 0
    assert result.win_rate == Decimal("0.0")


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_run_with_trades_profit(
    mock_get_datetime, sample_csv_data, mock_strategy_factory, patched_bt_result_cls
):
    strat = mock_strategy_factory()
    starting_balance = Decimal("1000.0")
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    result = backtest.run()

    assert isinstance(result, BacktestResult)
    k = backtest._om._leverage * Decimal("10.0")
    expected_total_pnl_calculated = (
        k * (Decimal("103.5") - Decimal("101.5")) / Decimal("101.5")
    )

    assert result.total_pnl == pytest.approx(expected_total_pnl_calculated)
    assert result.starting_balance == starting_balance
    assert result.end_balance == pytest.approx(
        starting_balance + expected_total_pnl_calculated
    )
    assert result.total_trades == 1
    assert result.win_rate == Decimal("1.0")


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
            "open": [
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
            ],
            "high": [
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
                Decimal("105"),
            ],
            "low": [
                Decimal("99"),
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
            ],
            "close": [
                Decimal("105.0"),
                Decimal("104.0"),
                Decimal("103.0"),
                Decimal("102.0"),
                Decimal("101.0"),
            ],
        }
    )
    df_path = tmp_path / "test_data_loss.csv"
    df.to_csv(df_path, index=False)

    strat = mock_strategy_factory()
    starting_balance = Decimal("1000.0")
    backtest = Backtest(
        strat=strat, df_path=str(df_path), starting_balance=starting_balance
    )

    result = backtest.run()

    total_value = backtest._om._leverage * Decimal("10")
    expected_total_pnl_calculated = total_value * (
        (Decimal("102.0") - Decimal("104.0")) / Decimal("104.0")
    )

    assert result.total_pnl == pytest.approx(expected_total_pnl_calculated)
    assert result.starting_balance == starting_balance
    assert result.end_balance == pytest.approx(
        starting_balance + expected_total_pnl_calculated
    )
    assert result.total_trades == 1
    assert result.win_rate == 0.0


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
                    amount=Decimal("10.0"),
                    price=tick.last,
                )

    strat = OpenOnlyStrategy(
        type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
    )
    starting_balance = Decimal("1000.0")
    backtest = Backtest(
        strat=strat, df_path=sample_csv_data, starting_balance=starting_balance
    )

    result = backtest.run()

    assert len(strat._om._positions) == 1
    open_pos = list(strat._om._positions.values())[0]

    assert result.total_pnl == Decimal("0.0")  # No positions were actually closed
    assert result.starting_balance == starting_balance
    assert result.end_balance == pytest.approx(starting_balance)
    assert result.total_trades == 1
    assert result.win_rate == Decimal("0.0")


def test_backtest_chunking(tmp_path, mock_strategy_factory):
    num_rows = 2500
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(
                pd.date_range("2023-01-01", periods=num_rows, freq="min")
            ),
            "open": [Decimal(str(i)) for i in range(100, 100 + num_rows)],
            "high": [Decimal(str(i)) for i in range(101, 101 + num_rows)],
            "low": [Decimal(str(i)) for i in range(99, 99 + num_rows)],
            "close": [
                Decimal(str(i)) + Decimal("0.5") for i in range(100, 100 + num_rows)
            ],
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


@patch(
    "lib.order_managers.demo_futures_order_manager.get_datetime",
    return_value=datetime(2023, 1, 1, 12, 0, 0),
)
def test_backtest_run_with_sl_tp_triggered(
    mock_get_datetime, sample_csv_data, tmp_path, mock_strategy_factory, monkeypatch
):
    monkeypatch.setattr("src.lib.backtest.PositionStatus", PositionStatus)
    monkeypatch.setattr("src.lib.backtest.OrderType", OrderType)
    monkeypatch.setattr(
        "src.lib.order_managers.demo_futures_order_manager.PositionStatus",
        PositionStatus,
    )
    monkeypatch.setattr(
        "src.lib.order_managers.demo_futures_order_manager.OrderType", OrderType
    )
    monkeypatch.setattr("src.lib.order_managers.demo_futures_order_manager.Side", Side)
    """
    Test that the backtest correctly closes positions when SL or TP is hit.
    """
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
            "open": [
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
            ],
            "high": [
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
                Decimal("105"),
            ],
            "low": [
                Decimal("99"),
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
            ],
            "close": [
                Decimal("100.5"),
                Decimal("100"),
                Decimal("102.5"),
                Decimal("103.5"),
                Decimal("104.5"),
            ],
        }
    )
    df_path = tmp_path / "sl_tp_test.csv"
    df.to_csv(df_path, index=False)

    class SLTPStrategy(Strategy):
        def __init__(self, *, type, platform, instrument, pip_size=0.0001):
            super().__init__(
                type=type, platform=platform, instrument=instrument, pip_size=pip_size
            )
            self._placed = False

        def run(self, tick: Tick):
            if not self._placed:
                self._placed = True
                self._om.open_position(
                    instrument=self._instrument,
                    side=Side.BID,
                    order_type=OrderType.MARKET,
                    amount=Decimal("10.0"),
                    price=tick.last,
                    sl_price=Decimal("100"),
                    tp_price=Decimal("102.5"),
                )

    strat = SLTPStrategy(
        type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
    )
    starting_balance = Decimal("1000.0")
    backtest = Backtest(
        strat=strat, df_path=str(df_path), starting_balance=starting_balance
    )

    result = backtest.run()

    assert result.total_trades == 1
    pos = strat._om._closed_positions[0]

    assert result.total_pnl == pytest.approx(
        (Decimal("100") - Decimal("100.5"))
        / Decimal("100.5")
        * pos.starting_amount
        * strat._om._leverage
    )
    assert result.win_rate == 0

    # Test scenario where TP is hit, SL is not.
    df_tp_only = pd.DataFrame(
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
            "open": [
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
            ],
            "high": [
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
                Decimal("105"),
            ],
            "low": [
                Decimal("99"),
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
            ],
            "close": [
                Decimal("100.5"),
                Decimal("101.5"),
                Decimal("102.0"),
                Decimal("103.0"),
                Decimal("104.0"),
            ],
        }
    )
    df_tp_only_path = tmp_path / "tp_only_test.csv"
    df_tp_only.to_csv(df_tp_only_path, index=False)

    class TPOnlyStrategy(Strategy):
        def __init__(self, *, type, platform, instrument, pip_size=0.0001):
            super().__init__(
                type=type, platform=platform, instrument=instrument, pip_size=pip_size
            )
            self._placed = False

        def run(self, tick: Tick):
            if not self._placed:
                self._placed = True

                self._om.open_position(
                    instrument=self._instrument,
                    side=Side.BID,
                    order_type=OrderType.MARKET,
                    amount=Decimal("10.0"),
                    price=tick.last,
                    tp_price=Decimal("102.0"),
                )

    strat_tp_only = TPOnlyStrategy(
        type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
    )
    backtest_tp_only = Backtest(
        strat=strat_tp_only,
        df_path=str(df_tp_only_path),
        starting_balance=Decimal("1000.0"),
    )

    result_tp_only = backtest_tp_only.run()

    assert result_tp_only.total_trades == 1
    assert result_tp_only.total_pnl == pytest.approx(
        (Decimal("102") - Decimal("100.5"))
        / Decimal("100.5")
        * pos.starting_amount
        * strat._om._leverage
    )
    assert result_tp_only.win_rate == Decimal("1.0")


def test_backtest_with_multiple_positions_and_closures(
    sample_csv_data, tmp_path, mock_strategy_factory, monkeypatch
):
    """
    Test the backtest with a strategy that opens multiple positions and they are closed.
    """
    monkeypatch.setattr("src.lib.backtest.PositionStatus", PositionStatus)
    monkeypatch.setattr("src.lib.backtest.OrderType", OrderType)
    monkeypatch.setattr(
        "src.lib.order_managers.demo_futures_order_manager.PositionStatus",
        PositionStatus,
    )
    monkeypatch.setattr(
        "src.lib.order_managers.demo_futures_order_manager.OrderType", OrderType
    )
    monkeypatch.setattr("src.lib.order_managers.demo_futures_order_manager.Side", Side)

    df_multi_adjusted = pd.DataFrame(
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
            "open": [
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
            ],
            "high": [
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
                Decimal("104"),
                Decimal("105"),
            ],
            "low": [
                Decimal("99"),
                Decimal("100"),
                Decimal("101"),
                Decimal("102"),
                Decimal("103"),
            ],
            "close": [
                Decimal("100.5"),
                Decimal("101.5"),
                Decimal("102.5"),
                Decimal("101.2"),
                Decimal("101.0"),
            ],
        }
    )
    df_multi_adjusted_path = tmp_path / "multi_pos_adjusted_test.csv"
    df_multi_adjusted.to_csv(df_multi_adjusted_path, index=False)

    class MultiPosStrategyAdjusted(Strategy):
        def __init__(self, *, type, platform, instrument, pip_size=0.0001):
            super().__init__(
                type=type, platform=platform, instrument=instrument, pip_size=pip_size
            )
            self._placed_a = False
            self._placed_b = False

        def run(self, tick: Tick):
            if len(self._om._positions) == 0 and not self._placed_a:
                self._placed_a = True
                self._om.open_position(
                    instrument=self._instrument,
                    side=Side.BID,
                    order_type=OrderType.MARKET,
                    amount=Decimal("10.0"),
                    price=tick.last,
                    sl_price=Decimal("99.0"),
                    tp_price=Decimal("102.5"),
                )
            elif len(self._om._positions) == 1 and not self._placed_b:
                self._placed_b = True
                self._om.open_position(
                    instrument=self._instrument,
                    side=Side.BID,
                    order_type=OrderType.MARKET,
                    amount=Decimal("5.0"),
                    price=tick.last,
                    sl_price=Decimal("101"),
                    tp_price=Decimal("102.0"),
                )

    strat_adj = MultiPosStrategyAdjusted(
        type=MagicMock(), platform=TradingPlatform.DEMO_FUTURES, instrument="EURUSD"
    )
    backtest_adj = Backtest(
        strat=strat_adj,
        df_path=str(df_multi_adjusted_path),
        starting_balance=Decimal("1000.0"),
    )

    result_adj = backtest_adj.run()

    lev = strat_adj._om._leverage
    first_pnl = (
        Decimal("10.0") * lev * (Decimal("102.5") - Decimal("100.5")) / Decimal("100.5")
    )
    second_pnl = (
        Decimal("5.0") * lev * (Decimal("101") - Decimal("101.5")) / Decimal("101.5")
    )
    total_pnl = second_pnl + first_pnl

    assert result_adj.total_trades == 2
    assert result_adj.total_pnl == pytest.approx(total_pnl)
    assert result_adj.win_rate == Decimal("1")
