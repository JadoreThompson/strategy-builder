from lib.typing import OHLC, BullishBOS, BearishBOS


def bullish_bos(candles: tuple[OHLC, ...]) -> BullishBOS:
    """
    Detect the latest bullish Break of Structure (BOS) in OHLC candles.

    Args:
        candles (tuple[OHLC, ...]): Sequence of OHLC candles.

    Returns:
        BullishBOS: Contains:
            - type (str): 'bullish'
            - present (bool): BOS occurred?
            - first_low_idx (int | None): Index of first swing low.
            - high_idx (int | None): Index of swing high.
            - second_low_idx (int | None): Index of second swing low.
            - breakout_idx (int | None): Index of candle breaking the high.
    """
    n = len(candles)
    first_low, high, second_low = None, None, None
    first_low_idx, high_idx, second_low_idx = None, None, None

    for i in range(n - 2, 0, -1):
        first, second, third = candles[i - 1], candles[i], candles[i + 1]

        if first.low >= second.low <= third.low:
            second_low = second.low
            second_low_idx = i
            first_low_idx, high_idx = None, None
            first_low, high = None, None
        elif high is None and first.high <= second.high >= third.high:
            high = second.high
            high_idx = i
        elif first_low is None and first.low >= second.low <= third.low:
            first_low = second.low
            first_low_idx = i
            break

    present = False
    breakout_idx = None
    if first_low is not None and high is not None and second_low is not None:
        for i in range(second_low_idx, n):
            candle = candles[i]
            if candle.open < high and candle.close > high:
                present = True
                breakout_idx = i
                break

    return BullishBOS(
        type="bullish",
        present=present,
        first_low_idx=first_low_idx,
        high_idx=high_idx,
        second_low_idx=second_low_idx,
        breakout_idx=breakout_idx,
    )


def bearish_bos(candles: tuple[OHLC, ...]) -> BearishBOS:
    """
    Detect the latest bearish Break of Structure (BOS) in OHLC candles.

    Args:
        candles (tuple[OHLC, ...]): Sequence of OHLC candles.

    Returns:
        BearishBOS: Contains:
            - type (str): 'bearish'
            - present (bool): BOS occurred?
            - first_high_idx (int | None): Index of first swing high.
            - low_idx (int | None): Index of swing low.
            - second_high_idx (int | None): Index of second swing high.
            - breakout_idx (int | None): Index of candle breaking the low.
    """
    n = len(candles)
    first_high, low, second_high = None, None, None
    first_high_idx, low_idx, second_high_idx = None, None, None

    for i in range(n - 2, 0, -1):
        first, second, third = candles[i - 1], candles[i], candles[i + 1]

        if second_high is None and first.high <= second.high >= third.high:
            second_high = second.high
            second_high_idx = i
            first_high_idx, low_idx = None, None
            first_high, low = None, None
        elif low is None and first.low >= second.low <= third.low:
            low = second.low
            low_idx = i
        elif first_high is None and first.high <= second.high >= third.high:
            first_high = second.high
            first_high_idx = i
            break

    present = False
    breakout_idx = None
    if first_high is not None and low is not None and second_high is not None:
        for i in range(second_high_idx, n):
            candle = candles[i]
            if candle.open > low and candle.close < low:
                present = True
                breakout_idx = i
                break

    return BearishBOS(
        type="bearish",
        present=present,
        first_high_idx=first_high_idx,
        low_idx=low_idx,
        second_high_idx=second_high_idx,
        breakout_idx=breakout_idx,
    )
