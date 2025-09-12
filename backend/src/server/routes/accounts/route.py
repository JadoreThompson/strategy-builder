from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db_models import Accounts
from server.dependencies import depends_db_sess, depends_jwt
from server.typing import JWTPayload
from .models import AccountCreate, AccountResponse, AccountDetailResponse


route = APIRouter(prefix="/accounts", tags=["accounts"])


@route.post("/", response_model=AccountResponse)
async def create_account(
    body: AccountCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    account = await db_sess.scalar(
        insert(Accounts)
        .values(
            user_id=jwt.sub,
            name=body.name,
            login=body.login,
            password=body.password, # TODO: Hash
            server=body.server,
            platform=body.platform,
        )
        .returning(Accounts)
    )
    await db_sess.commit()
    
    return AccountResponse(
        account_id=account.account_id,
        name=account.name,
        platform=account.platform,
        created_at=account.created_at,
    )


@route.get("/", response_model=list[AccountResponse])
async def get_accounts(
    name: str | None = None,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    q = select(Accounts).where(Accounts.user_id == jwt.sub)

    if name:
        q = q.where(Accounts.name.like(f"%{name}%"))

    res = await db_sess.scalars(q)
    accounts = res.all()
    return [
        AccountResponse(
            account_id=acc.account_id,
            name=acc.name,
            platform=acc.platform,
            created_at=acc.created_at,
        )
        for acc in accounts
    ]


@route.get("/{account_id}", response_model=AccountDetailResponse)
async def get_account(
    account_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    account = await db_sess.scalar(
        select(Accounts).where(
            Accounts.account_id == account_id, Accounts.user_id == jwt.sub
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountDetailResponse(
        account_id=account.account_id,
        name=account.name,
        login=account.login,
        server=account.server,
        platform=account.platform,
        created_at=account.created_at,
    )


@route.delete("/{account_id}")
async def delete_account(
    account_id: UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    account = await db_sess.scalar(
        select(Accounts).where(
            Accounts.account_id == account_id, Accounts.user_id == jwt.sub
        )
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await db_sess.delete(account)
    await db_sess.commit()
    return {"message": "Successfully deleted account"}
