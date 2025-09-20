from trading_lib.typing import OHLC, MSS


def detect_bullish_mss(ohlcs: tuple[OHLC]) -> list[MSS]:
    n = len(ohlcs)
    swing_low_idx, swing_high_idx = None, None
    mss = []
    swing_highs, swing_lows = [], []
    expecting_low = False

    for i in range(1, n - 1):
        prev, cur, nxt = ohlcs[i - 1], ohlcs[i], ohlcs[i + 1]

        if prev.high < cur.high > nxt.high:
            if not expecting_low:
                swing_high_idx = i
                expecting_low = True
            elif swing_high_idx is not None and cur.high > ohlcs[swing_high_idx].high:
                swing_high_idx = i
                expecting_low = True
        elif prev.low > cur.low < nxt.low:
            if expecting_low:
                swing_low_idx = i
                expecting_low = False
            elif swing_low_idx is not None and cur.low < ohlcs[swing_low_idx].low:
                swing_low_idx = i
                expecting_low = False

        if (
            swing_low_idx is not None
            and swing_high_idx is not None
            and swing_high_idx < swing_low_idx
        ):
            swing_highs.append(swing_high_idx)
            swing_lows.append(swing_low_idx)
            swing_high_idx, swing_low_idx = None, None

    inds: list[tuple[int, int, int]] = []
    for i in range(len(swing_highs)):
        if i + 1 >= len(swing_highs):
            inds.append((swing_highs[i], swing_lows[i], n))
        else:
            inds.append((swing_highs[i], swing_lows[i], swing_highs[i + 1]))

    for high_ind, low_ind, end_ind in inds:
        for j in range(low_ind, end_ind):
            if ohlcs[j].close > ohlcs[high_ind].high:
                mss.append(
                    MSS(
                        type="bullish",
                        present=True,
                        swing_high_idx=high_ind,
                        swing_low_idx=low_ind,
                        breakout_idx=j,
                    )
                )
                break

    return mss


def detect_bearish_mss(ohlcs: tuple[OHLC]) -> list[MSS]:
    n = len(ohlcs)
    swing_low_idx, swing_high_idx = None, None
    mss = []
    swing_highs, swing_lows = [], []
    expecting_high = False

    for i in range(1, n - 1):
        prev, cur, nxt = ohlcs[i - 1], ohlcs[i], ohlcs[i + 1]

        if prev.low > cur.low < nxt.low:
            if not expecting_high:
                swing_low_idx = i
                expecting_high = True
            elif swing_low_idx is not None and cur.low < ohlcs[swing_low_idx].low:
                swing_low_idx = i
                expecting_high = True
        elif prev.high < cur.high > nxt.high:
            if expecting_high:
                swing_high_idx = i
                expecting_high = False
            elif swing_high_idx is not None and cur.high > ohlcs[swing_high_idx].high:
                swing_high_idx = i
                expecting_high = False

        if (
            swing_low_idx is not None
            and swing_high_idx is not None
            and swing_high_idx > swing_low_idx
        ):
            swing_highs.append(swing_high_idx)
            swing_lows.append(swing_low_idx)

    inds: list[tuple[int, int, int]] = []
    for i in range(len(swing_lows)):
        if i + 1 >= len(swing_lows):
            inds.append((swing_highs[i], swing_lows[i], n))
        else:
            inds.append((swing_highs[i], swing_lows[i], swing_lows[i + 1]))

    for high_ind, low_ind, end_ind in inds:
        for j in range(high_ind, end_ind):
            if ohlcs[j].close < ohlcs[low_ind].low:
                mss.append(
                    MSS(
                        type="bearish",
                        present=True,
                        swing_high_idx=high_ind,
                        swing_low_idx=low_ind,
                        breakout_idx=j,
                    )
                )
                break

    return mss
