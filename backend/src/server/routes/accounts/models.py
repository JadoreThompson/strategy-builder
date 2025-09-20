from datetime import datetime
from uuid import UUID

from core.typing import CustomBaseModel
from trading_lib.enums import TradingPlatform


class AccountCreate(CustomBaseModel):
    name: str
    login: str
    password: str
    server: str
    platform: TradingPlatform


class AccountResponse(CustomBaseModel):
    account_id: UUID
    name: str
    platform: str
    created_at: datetime


class AccountDetailResponse(AccountResponse):
    login: str
    server: str


class AccountUpdate(CustomBaseModel):
    name: str | None = None
    login: str | None = None
    password: str | None = None
    server: str | None = None
    platform: str | None = None
