from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import PAGE_SIZE
from db_models import Accounts
from server.dependencies import depends_db_sess, depends_jwt
from server.models import PaginatedResponse
from server.typing import JWTPayload
from .models import AccountCreate, AccountResponse, AccountDetailResponse, AccountUpdate


route = APIRouter(prefix="/accounts", tags=["accounts"])


@route.post("/", response_model=AccountResponse)
async def create_account(
    body: AccountCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    res = await db_sess.execute(
        insert(Accounts)
        .values(
            user_id=jwt.sub,
            name=body.name,
            login=body.login,
            password=body.password,  # TODO: Hash
            server=body.server,
            platform=body.platform.value,
        )
        .returning(Accounts)
    )

    account = res.scalar()
    res = AccountResponse(
        account_id=account.account_id,
        name=account.name,
        platform=account.platform,
        created_at=account.created_at,
    )

    await db_sess.commit()
    return res


@route.get("/", response_model=PaginatedResponse[AccountDetailResponse])
async def get_accounts(
    name: str | None = None,
    page: int = 1,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(depends_db_sess),
):
    q = select(Accounts).where(Accounts.user_id == jwt.sub)

    if name:
        q = q.where(Accounts.name.like(f"%{name}%"))

    res = await db_sess.scalars(q.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE + 1))
    accounts = res.all()

    return PaginatedResponse[AccountDetailResponse](
        page=page,
        size=len(accounts),
        has_next=len(accounts) > PAGE_SIZE,
        data=[
            AccountDetailResponse(
                account_id=acc.account_id,
                name=acc.name,
                login=acc.login,
                server=acc.server,
                platform=acc.platform,
                created_at=acc.created_at,
            )
            for acc in accounts
        ],
    )


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


@route.patch("/{account_id}", response_model=AccountDetailResponse)
async def update_account(
    account_id: UUID,
    body: AccountUpdate,
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

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    refreshed = await db_sess.scalar(
        update(Accounts)
        .where(Accounts.account_id == account_id)
        .values(**update_data)
        .returning(Accounts)
    )

    res = AccountDetailResponse(
        account_id=refreshed.account_id,
        name=refreshed.name,
        login=refreshed.login,
        server=refreshed.server,
        platform=refreshed.platform,
        created_at=refreshed.created_at,
    )

    await db_sess.commit()

    return res


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
