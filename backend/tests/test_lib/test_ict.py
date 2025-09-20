import pytest

from src.trading_lib.ict import fvg
from lib.ict.mss import detect_bullish_mss, detect_bearish_mss
from src.trading_lib.typing import OHLC, MSS, FVG


@pytest.fixture
def ohlc_candles():
    """Provides a generic set of OHLC candles for testing."""
    return (
        OHLC(open=100, high=105, low=99, close=104, time=1),  # 0
        OHLC(open=104, high=108, low=103, close=107, time=2),  # 1
        OHLC(open=107, high=110, low=106, close=109, time=3),  # 2
        OHLC(open=109, high=112, low=108, close=111, time=4),  # 3
        OHLC(open=111, high=115, low=110, close=114, time=5),  # 4
    )


def test_fvg_bullish():
    """Tests detection of a bullish Fair Value Gap."""
    candles = [
        OHLC(open=100, high=105, low=99, close=104, time=1),
        OHLC(open=106, high=110, low=105.5, close=109, time=2),
        OHLC(open=108, high=112, low=107, close=111, time=3),
    ]
    result = fvg(candles)
    assert result.above == 107
    assert result.below == 105


def test_fvg_bearish():
    """Tests detection of a bearish Fair Value Gap."""
    candles = [
        OHLC(open=112, high=113, low=108, close=109, time=1),
        OHLC(open=107, high=107.5, low=104, close=105, time=2),
        OHLC(open=105, high=106, low=102, close=103, time=3),
    ]
    result = fvg(candles)
    assert result.above == 108
    assert result.below == 106


def test_fvg_no_gap():
    """Tests scenario with no Fair Value Gap."""
    candles = [
        OHLC(open=100, high=105, low=99, close=104, time=1),
        OHLC(open=104, high=106, low=103, close=105, time=2),
        OHLC(open=105, high=107, low=104, close=106, time=3),
    ]
    result = fvg(candles)
    assert result is None


def test_fvg_invalid_input():
    """Tests that fvg raises ValueError for incorrect number of candles."""
    candles = [OHLC(open=1, high=2, low=0, close=1, time=1)]
    with pytest.raises(ValueError):
        fvg(candles)


def test_bullish_bos_detected():
    """Tests detection of a clear bullish Break of Structure."""
    candles = (
        OHLC(open=1, high=10, low=8, close=1, time=1),
        OHLC(open=1, high=9, low=5, close=1, time=2),  # First Low
        OHLC(open=1, high=10, low=8, close=1, time=3),
        OHLC(open=1, high=15, low=10, close=1, time=4),  # High
        OHLC(open=1, high=14, low=12, close=1, time=5),
        OHLC(open=1, high=13, low=7, close=1, time=6),  # Second Low
        OHLC(open=12, high=14, low=12, close=14, time=7),
        OHLC(open=14, high=18, low=14, close=16, time=8),  # Breakout
    )
    result = detect_bullish_mss(candles)
    assert result
    assert result[0].swing_high_idx == 3
    assert result[0].swing_low_idx == 5
    assert result[0].breakout_idx == 7


def test_bullish_bos_not_detected():
    """Tests scenario where no bullish BOS occurs."""
    candles = (
        OHLC(open=1, high=10, low=8, close=1, time=1),
        OHLC(open=1, high=9, low=5, close=1, time=2),
        OHLC(open=1, high=10, low=8, close=1, time=3),
        OHLC(open=1, high=15, low=10, close=1, time=4),
        OHLC(open=1, high=14, low=12, close=1, time=5),
        OHLC(open=1, high=13, low=7, close=1, time=6),
        OHLC(open=1, high=14, low=12, close=1, time=7),  # No breakout
    )
    result = detect_bullish_mss(candles)
    assert not result


def test_bearish_bos_detected():
    """Tests detection of a clear bearish Break of Structure."""
    candles = (
        OHLC(open=1, high=14, low=10, close=1, time=2),
        OHLC(open=1, high=12, low=9, close=1, time=3),  # Low
        OHLC(open=1, high=13, low=10, close=1, time=4),
        OHLC(open=1, high=18, low=1, close=9, time=5),  # High
        OHLC(open=1, high=17, low=1, close=9, time=6),
        OHLC(open=8, high=10, low=3, close=4, time=7),  # Breakout
    )
    result = detect_bearish_mss(candles)

    assert result
    assert result[-1].swing_low_idx == 1
    assert result[-1].swing_high_idx == 3
    assert result[-1].breakout_idx == 5


def test_bearish_bos_not_detected():
    """Tests scenario where no bearish BOS occurs."""
    candles = (
        OHLC(open=1, high=15, low=1, close=1, time=1),
        OHLC(open=1, high=14, low=1, close=1, time=2),
        OHLC(open=1, high=12, low=5, close=1, time=3),
        OHLC(open=1, high=13, low=1, close=1, time=4),
        OHLC(open=1, high=18, low=1, close=1, time=5),
        OHLC(open=1, high=17, low=6, close=1, time=6),  # No breakout
    )
    result = detect_bearish_mss(candles)
    assert not result
