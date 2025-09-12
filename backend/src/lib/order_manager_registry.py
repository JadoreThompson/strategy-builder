from lib.enums import TradingPlatform
from lib.order_managers import FuturesOrderManager, MT5FuturesOrderManager


class OrderManagerRegistry:
    _managers = {
        TradingPlatform.MT5: MT5FuturesOrderManager,
    }

    @classmethod
    def get(cls, platform: TradingPlatform) -> FuturesOrderManager | None:
        manager = cls._managers.get(platform)
        if manager:
            return manager()
