"""SQL модуля bonus."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.bonus.models import BonusAccount, BonusTransaction


async def ensure_account(session: AsyncSession, phone: str, guest_token: str) -> BonusAccount:
    """Счёт с токеном первого/последнего заказа. Гонку параллельных созданий гасит ON CONFLICT."""
    stmt = pg_insert(BonusAccount).values(
        phone=phone, balance=0, lifetime_spent=0, guest_token=guest_token
    )
    await session.execute(stmt.on_conflict_do_nothing(index_elements=["phone"]))
    res = await session.execute(select(BonusAccount).where(BonusAccount.phone == phone))
    account = res.scalar_one()
    account.guest_token = guest_token
    await session.flush()
    return account


async def get_account(session: AsyncSession, phone: str) -> BonusAccount | None:
    res = await session.execute(select(BonusAccount).where(BonusAccount.phone == phone))
    return res.scalar_one_or_none()


async def get_account_for_update(session: AsyncSession, phone: str) -> BonusAccount | None:
    res = await session.execute(
        select(BonusAccount).where(BonusAccount.phone == phone).with_for_update()
    )
    return res.scalar_one_or_none()


async def get_account_by_id_for_update(
    session: AsyncSession, account_id: int
) -> BonusAccount | None:
    res = await session.execute(
        select(BonusAccount).where(BonusAccount.id == account_id).with_for_update()
    )
    return res.scalar_one_or_none()


async def transactions(
    session: AsyncSession, account_id: int, limit: int = 50
) -> list[BonusTransaction]:
    res = await session.execute(
        select(BonusTransaction)
        .where(BonusTransaction.account_id == account_id)
        .order_by(BonusTransaction.id.desc())
        .limit(limit)
    )
    return list(res.scalars().all())


async def txn_for_order(session: AsyncSession, order_id: int, type: str) -> BonusTransaction | None:
    res = await session.execute(
        select(BonusTransaction).where(
            BonusTransaction.order_id == order_id, BonusTransaction.type == type
        )
    )
    return res.scalar_one_or_none()
