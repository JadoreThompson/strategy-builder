from datetime import datetime
from uuid import UUID

from lib.enums import TradingPlatform
from core.typing import CustomBaseModel


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
