def calc_price_change(open_price: float, close_price: float):
    return open_price * (close_price - open_price) / open_price
