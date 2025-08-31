from lib.enums import TradingPlatform
from lib.order_managers import FuturesOrderManager, MT5OrderManager, SpotOrderManager


class OrderManagerRegistry:
    _managers = {TradingPlatform.MT5: MT5OrderManager}

    @classmethod
    def get(
        cls, platform: TradingPlatform
    ) -> SpotOrderManager | FuturesOrderManager | None:
        manager = cls._managers.get(platform)
        if manager:
            return manager()
