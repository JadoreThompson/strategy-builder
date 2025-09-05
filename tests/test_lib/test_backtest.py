import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.lib.backtest import Backtest
from src.lib.strategy import Strategy
from src.core.enums import Side, OrderType, PositionStatus
from src.lib.typing import Position, Tick, BacktestResult


class MockStrategy(Strategy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_calls = 0

    def run(self, tick: Tick):
        self.run_calls += 1
        if self.run_calls == 1:
            self._om.open_position("TEST", Side.BID, OrderType.MARKET, Decimal("10"))

    def shutdown(self):
        pass

    def startup(self):
        pass


@pytest.fixture
def sample_df_backtest():
    """Provides a DataFrame for a full backtest run."""
    data = {"close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]}
    index = pd.to_datetime([f"2023-01-01 12:0{i}" for i in range(6)])
    return pd.DataFrame(data, index=index)



@patch("src.lib.order_managers.backtest_futures_order_manager.OrderType", OrderType)
@patch("src.lib.backtest.BacktestResult", BacktestResult)
def test_backtest_run(sample_df_backtest):
    """
    Tests a full run of the backtest, ensuring the strategy is called
    and results are generated.
    """
    strat = MockStrategy(type=MagicMock(), platform=MagicMock(), instrument="TEST")

    with patch("src.lib.strategy.OrderManagerRegistry.get", return_value=None):
        strat = MockStrategy(type=MagicMock(), platform=MagicMock(), instrument="TEST")

    bt = Backtest(
        strat=strat, df=sample_df_backtest, starting_balance=10000, leverage=10
    )

    mock_pos = Position(
        id="p1",
        instrument="TEST",
        side=Side.BID,
        order_type=OrderType.MARKET,
        price=100.0,
        starting_amount=Decimal("10"),
    )
    bt._om._exchange.open_position = MagicMock(return_value=mock_pos)

    result = bt.run()

    assert strat.run_calls == 6  # Called for each tick in the df

    assert len(bt._om.positions) == 1
    pos = bt._om.positions[0]

    assert isinstance(result, BacktestResult)
    assert result.starting_balance == 10000
    assert pytest.approx(result.total_pnl) == 0
    assert pytest.approx(result.end_balance) == 10000
    assert result.total_trades == 1
    assert result.win_rate == 0  # The trade is still open


@patch("src.lib.backtest.PositionStatus", PositionStatus)
@patch("src.lib.exchanges.backtest_futures_exchange.OrderType", OrderType)
@patch("src.lib.order_managers.backtest_futures_order_manager.OrderType", OrderType)
def test_backtest_run_with_tp_hit(sample_df_backtest):
    """
    Tests that a position is closed when its Take Profit is hit during the run.
    """

    class TPStrategy(Strategy):
        def run(self, tick: Tick):
            if not self._om._closed_positions:
                self._om.open_position(
                    "TEST", Side.BID, OrderType.MARKET, Decimal("10"), tp_price=105.0
                )

        def shutdown(self):
            pass

        def startup(self):
            pass

    with patch("src.lib.strategy.OrderManagerRegistry.get", return_value=None):
        strat = TPStrategy(type=MagicMock(), platform=MagicMock(), instrument="TEST")

    bt = Backtest(
        strat=strat, df=sample_df_backtest, starting_balance=10000, leverage=10
    )

    mock_pos = Position(
        id="p1",
        instrument="TEST",
        side=Side.BID,
        order_type=OrderType.MARKET,
        price=100.0,
        starting_amount=Decimal("10"),
        tp_price=105.0,
        status=PositionStatus.OPEN,
    )
    bt._om._exchange.open_position = MagicMock(return_value=mock_pos)

    result = bt.run()

    assert len(bt._om.positions) == 0
    assert len(bt._om._closed_positions) == 1

    assert result.total_trades == 1
    assert result.win_rate == 1  # A winning trade
    assert pytest.approx(result.total_pnl) == 5
    assert pytest.approx(result.end_balance) == 10005


def test_get_backtest_result():
    """
    Tests the _get_backtest_result method's calculations.
    """
    mock_strat = MagicMock()
    bt = Backtest(strat=mock_strat, starting_balance=1000)
    om = bt._om

    om._balance = Decimal("1500")

    win_pos = Position(
        id="p1",
        instrument="A",
        side=Side.BID,
        order_type=OrderType.MARKET,
        starting_amount=Decimal(1),
        realised_pnl=Decimal("600"),
    )
    
    loss_pos = Position(
        id="p2",
        instrument="A",
        side=Side.BID,
        order_type=OrderType.MARKET,
        starting_amount=Decimal(1),
        realised_pnl=Decimal("-100"),
    )
    
    open_pos = Position(
        id="p3",
        instrument="A",
        side=Side.BID,
        order_type=OrderType.MARKET,
        starting_amount=Decimal(1),
        unrealised_pnl=Decimal("50"),
    )

    om._closed_positions = [win_pos, loss_pos]
    om._positions = {"p3": open_pos}

    open_pos.realised_pnl = open_pos.unrealised_pnl

    result = bt._get_backtest_result()

    assert result.starting_balance == 1000
    assert result.end_balance == Decimal("1500")
    assert result.total_trades == 3
    assert result.win_rate == 1
    assert result.total_pnl == Decimal("600") + Decimal("-100") + Decimal("50")
