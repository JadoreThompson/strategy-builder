from lib.enums import TradingPlatform
from lib.order_managers import (
    FuturesOrderManager,
    MT5OrderManager,
    DemoFuturesOrderManager,
)


class OrderManagerRegistry:
    _managers = {
        TradingPlatform.MT5: MT5OrderManager,
        TradingPlatform.DEMO_FUTURES: DemoFuturesOrderManager,
    }

    @classmethod
    def get(cls, platform: TradingPlatform) -> FuturesOrderManager | None:
        manager = cls._managers.get(platform)
        if manager:
            return manager()
