"""SQL модуля orders. Чужие таблицы не трогаем — каталог даёт menu.service."""

from datetime import date as date_cls
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import (
    ACTIVE_STATUSES,
    LocationDayCounter,
    Order,
    OrderItem,
    OrderStatusEvent,
    SlotLoad,
)


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.get(Order, order_id)


async def get_order_for_update(session: AsyncSession, order_id: int) -> Order | None:
    res = await session.execute(select(Order).where(Order.id == order_id).with_for_update())
    return res.scalar_one_or_none()


async def find_by_idempotency(session: AsyncSession, key: str) -> Order | None:
    res = await session.execute(select(Order).where(Order.idempotency_key == key))
    return res.scalar_one_or_none()


async def order_items(session: AsyncSession, order_id: int) -> list[OrderItem]:
    res = await session.execute(
        select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
    )
    return list(res.scalars().all())


async def active_orders_for_location(session: AsyncSession, location_id: int) -> list[Order]:
    res = await session.execute(
        select(Order)
        .where(Order.location_id == location_id, Order.status.in_(ACTIVE_STATUSES))
        .order_by(Order.pickup_at, Order.id)
    )
    return list(res.scalars().all())


async def get_slot_for_update(
    session: AsyncSession, location_id: int, slot_start: datetime
) -> SlotLoad | None:
    res = await session.execute(
        select(SlotLoad)
        .where(SlotLoad.location_id == location_id, SlotLoad.slot_start == slot_start)
        .with_for_update()
    )
    return res.scalar_one_or_none()


async def ensure_slot_row(session: AsyncSession, location_id: int, slot_start: datetime) -> None:
    """Создаёт строку слота, если нет. Гонку параллельных INSERT гасит ON CONFLICT."""
    stmt = pg_insert(SlotLoad).values(
        location_id=location_id, slot_start=slot_start, units_reserved=0
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["location_id", "slot_start"])
    await session.execute(stmt)


async def reserved_map(session: AsyncSession, location_id: int) -> dict[datetime, int]:
    res = await session.execute(select(SlotLoad).where(SlotLoad.location_id == location_id))
    return {row.slot_start: row.units_reserved for row in res.scalars().all()}


async def next_order_number(session: AsyncSession, location_id: int, day: date_cls) -> int:
    """Счётчик кода заказа за локальный день. Блокировка строки исключает дубли и дыры."""
    await session.execute(_counter_insert(location_id, day))
    res = await session.execute(
        select(LocationDayCounter)
        .where(LocationDayCounter.location_id == location_id, LocationDayCounter.day == day)
        .with_for_update()
    )
    counter = res.scalar_one()
    counter.last_n += 1
    await session.flush()
    return counter.last_n


def _counter_insert(location_id: int, day: date_cls):  # type: ignore[no-untyped-def]
    stmt = pg_insert(LocationDayCounter).values(location_id=location_id, day=day, last_n=0)
    return stmt.on_conflict_do_nothing(index_elements=["location_id", "day"])


async def add_status_event(
    session: AsyncSession, order_id: int, from_status: str | None, to_status: str, actor: str
) -> None:
    session.add(
        OrderStatusEvent(
            order_id=order_id, from_status=from_status, to_status=to_status, actor=actor
        )
    )
