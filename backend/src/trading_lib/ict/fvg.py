from trading_lib.typing import FVG, OHLC


def fvg(candles: list[OHLC]) -> FVG | None:
    if len(candles) != 3:
        raise ValueError("Must provide 3 candles.")

    first, last = candles[0], candles[2]

    if first.low > last.high:
        return FVG(above=first.low, below=last.high)
    if first.high < last.low:
        return FVG(above=last.low, below=first.high)
