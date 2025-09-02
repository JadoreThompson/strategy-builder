from aiohttp import ClientSession
from fastapi import APIRouter, Depends

from server.dependencies import depends_http_sess, depends_jwt
from server.typing import JWTPayload
from .models import StrategyCreate


route = APIRouter(prefix="/strategy", tags=["strategy"])


@route.post("/")
async def create_strategy(
    body: StrategyCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    http_sess: ClientSession = Depends(depends_http_sess),
): ...
