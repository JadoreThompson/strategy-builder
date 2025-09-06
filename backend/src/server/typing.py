from dataclasses import dataclass
from datetime import datetime


@dataclass
class JWTPayload:
    sub: str 
    exp: datetime
