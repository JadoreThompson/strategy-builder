import pytest
from unittest.mock import MagicMock, patch

from src.core.enums import StrategyType
from src.lib.enums import TradingPlatform
from src.lib.strategy import Strategy
from src.lib.typing import Tick


class TestStrategy(Strategy):
    def run(self, tick: Tick):
        pass
    def shutdown(self):
        super().shutdown()
    def startup(self):
        super().startup()


@patch('src.lib.strategy.OrderManagerRegistry.get')
def test_strategy_initialization(mock_get_om):
    """
    Tests that the Strategy class initializes correctly and retrieves the
    correct order manager from the registry.
    """
    mock_om = MagicMock()
    mock_get_om.return_value = mock_om
    
    strat = TestStrategy(
        type=StrategyType.FUTURES,
        platform=TradingPlatform.MT5,
        instrument="EURUSD"
    )

    mock_get_om.assert_called_once_with(TradingPlatform.MT5)
    assert strat._om is mock_om
    assert strat._type == StrategyType.FUTURES
    assert strat.type == StrategyType.FUTURES
    assert strat._instrument == "eurusd"

@patch('src.lib.strategy.OrderManagerRegistry.get')
def test_strategy_context_manager(mock_get_om):
    """
    Tests the __enter__ and __exit__ methods to ensure startup and shutdown
    are called.
    """
    mock_om = MagicMock()
    mock_get_om.return_value = mock_om
    
    strat = TestStrategy(
        type=StrategyType.FUTURES,
        platform=TradingPlatform.MT5,
        instrument="EURUSD"
    )

    with patch.object(strat, 'startup', wraps=strat.startup) as mock_startup, \
         patch.object(strat, 'shutdown', wraps=strat.shutdown) as mock_shutdown:
        
        with strat:
            mock_startup.assert_called_once()
            mock_shutdown.assert_not_called()
            mock_om.login.assert_called_once()
        
        mock_shutdown.assert_called_once()
