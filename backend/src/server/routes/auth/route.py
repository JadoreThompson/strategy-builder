from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db_models import Users
from server.dependencies import depends_db_sess
from server.services import JWTService
from .models import UserCreate, UserLogin


route = APIRouter(prefix="/auth", tags=["auth"])


@route.post("/register")
async def register(body: UserCreate, db_sess: AsyncSession = Depends(depends_db_sess)):
    res = await db_sess.execute(select(Users).where(Users.username == body.username))
    if res.first():
        return JSONResponse(
            status_code=401, content={"error": "User with username already exists."}
        )

    result = await db_sess.execute(
        insert(Users).values(username=body.username, password=body.password).returning(Users.user_id)
    )
    user_id = result.scalar_one()
    await db_sess.commit()

    return JWTService.set_cookie(user_id)


@route.post("/login")
async def login(body: UserLogin, db_sess: AsyncSession = Depends(depends_db_sess)):

    res = await db_sess.execute(
        select(Users.user_id).where(
            Users.password == body.password, Users.username == body.username
        )
    )
    user_id = res.scalar_one_or_none()

    if user_id is None:
        return JSONResponse(status_code=401, content={"error": "Invalid user."})

    return JWTService.set_cookie(user_id)
