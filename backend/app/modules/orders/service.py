"""Заказы и слоты (SPEC 5.4–5.7, 10.1). Резервирование — в транзакции с блокировкой."""

import json
from datetime import UTC, datetime, timedelta, tzinfo
from math import ceil
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.eventbus import EventBus
from app.core.security import body_hash, new_access_token
from app.core.time import WEEKDAYS
from app.modules.menu import pricing, validation
from app.modules.menu.models import Location
from app.modules.menu.service import CatalogData, load_catalog
from app.modules.menu.validation import ValidationError
from app.modules.orders import repository
from app.modules.orders.models import (
    CANCELLED,
    CONFIRMED,
    ON_SITE,
    PREPARING,
    READY,
    Order,
    OrderItem,
)
from app.modules.orders.schemas import (
    OrderCreateIn,
    OrderCreateOut,
    OrderItemOut,
    OrderOut,
    SlotOut,
    SlotsOut,
)

# Статусная машина (SPEC 5.5): из -> {в: {акторы}}.
TRANSITIONS: dict[str, dict[str, set[str]]] = {
    CONFIRMED: {"preparing": {"staff"}, "cancelled": {"customer", "staff"}},
    PREPARING: {"ready": {"staff"}, "cancelled": {"staff"}},
    READY: {"picked_up": {"staff"}},
}


def canonical_payload(payload: OrderCreateIn) -> str:
    return json.dumps(payload.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)


def ceil_to_step(local: datetime, step_min: int) -> datetime:
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    mins = ceil((local - midnight).total_seconds() / 60 / step_min) * step_min
    return midnight + timedelta(minutes=int(mins))


def parse_interval(value: Any) -> tuple[int, int] | None:
    """['08:00','22:00'] -> (480, 1320)."""
    try:
        open_s, close_s = value
        oh, om = map(int, str(open_s).split(":"))
        ch, cm = map(int, str(close_s).split(":"))
        return oh * 60 + om, ch * 60 + cm
    except (ValueError, TypeError):
        return None


def day_slots_utc(location: Location, now_utc: datetime) -> tuple[list[datetime], bool]:
    """Старты слотов на сегодня (UTC). Возвращает (слоты, точка_открыта_сегодня)."""
    try:
        tz = ZoneInfo(location.timezone)
    except Exception:
        return [], False
    local_now = now_utc.astimezone(tz)
    intervals = (location.opening_hours or {}).get(WEEKDAYS[local_now.weekday()]) or []
    if not intervals:
        return [], False
    earliest = ceil_to_step(
        local_now + timedelta(minutes=location.lead_time_min), location.slot_step_min
    )
    today = local_now.date()
    slots: list[datetime] = []
    for raw in intervals:
        parsed = parse_interval(raw)
        if parsed is None:
            continue
        open_min, close_min = parsed
        open_local = datetime(today.year, today.month, today.day, tzinfo=tz) + timedelta(
            minutes=open_min
        )
        close_local = datetime(today.year, today.month, today.day, tzinfo=tz) + timedelta(
            minutes=close_min
        )
        if close_local <= open_local:
            continue
        first = ceil_to_step(max(open_local, earliest), location.slot_step_min)
        tick = first
        while tick <= close_local:
            slots.append(tick.astimezone(UTC))
            tick += timedelta(minutes=location.slot_step_min)
    return sorted(set(slots)), True


async def get_slots(
    session: AsyncSession, location_id: int, units: int, now_utc: datetime
) -> SlotsOut:
    data = await load_catalog(session, location_id)
    loc = data.location
    if units > loc.slot_capacity:
        raise ValidationError("order_too_large", "Order exceeds slot capacity", {"units": units})
    starts, is_open = day_slots_utc(loc, now_utc)
    reserved = await repository.reserved_map(session, location_id)
    out: list[SlotOut] = []
    for start in starts:
        left = loc.slot_capacity - reserved.get(start, 0)
        out.append(SlotOut(start=start, available=left >= units, remaining=max(left, 0)))
    asap = next((s for s in out if s.available), None)
    return SlotsOut(location_id=location_id, open=is_open, units=units, asap=asap, slots=out)


def resolve_slot(
    loc: Location, units: int, mode: str, pickup_at: datetime | None, slots: SlotsOut
) -> tuple[datetime, bool]:
    """Возвращает (старт_слота_UTC, is_asap). Бросает ValidationError из SPEC."""
    by_start = {s.start: s for s in slots.slots}
    if mode == ON_SITE:
        if slots.asap is None:
            raise ValidationError("slot_unavailable", "No free slots today", {})
        return slots.asap.start, True
    # scheduled
    if pickup_at is None:
        raise ValidationError("validation_error", "pickup_at required for scheduled mode", {})
    want = pickup_at if pickup_at.tzinfo else pickup_at.replace(tzinfo=UTC)
    want = want.astimezone(UTC)
    slot = by_start.get(want)
    if slot is None:
        # Различаем «вне часов» и «занято»: есть ли такой старт в сетке вообще.
        raise ValidationError("outside_hours", "Pickup time is outside working hours", {})
    if not slot.available:
        raise ValidationError("slot_unavailable", "Slot is full", {})
    return want, False


def order_out(order: Order, items: list[OrderItem]) -> OrderOut:
    return OrderOut(
        id=order.id,
        code=order.code,
        location_id=order.location_id,
        status=order.status,
        mode=order.mode,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        comment=order.comment or "",
        pickup_at=order.pickup_at,
        is_asap=order.is_asap,
        total=order.total,
        currency=order.currency,
        payment_method=order.payment_method,
        bonus_applied=0,
        items=[
            OrderItemOut(
                product_id=i.product_id,
                product_name=i.product_name,
                quantity=i.quantity,
                unit_price=i.unit_price,
                options=list(i.options or []),
                line_total=i.line_total,
            )
            for i in items
        ],
        created_at=order.created_at,
    )


def _price_lines(
    data: CatalogData, payload: OrderCreateIn
) -> tuple[list[dict[str, Any]], int, int]:
    """Валидация + пересчёт цены на сервере. Возвращает (строки, total, units)."""
    lines: list[dict[str, Any]] = []
    totals: list[int] = []
    units = 0
    for item in payload.items:
        product = data.catalog.get(item.product_id)
        if product is None:
            raise ValidationError(
                "validation_error", "Unknown product", {"product_id": item.product_id}
            )
        deltas = validation.validate_line(product, list(item.option_ids), item.quantity)
        unit = pricing.unit_price(product.base_price, deltas)
        line = pricing.line_total(unit, item.quantity)
        db_product = data.products[item.product_id]
        lines.append(
            {
                "product_id": item.product_id,
                "product_name": db_product.name,
                "quantity": item.quantity,
                "unit_price": unit,
                "line_total": line,
                "options": [
                    {
                        "group": data.groups[data.options[oid].group_id].key,
                        "option": data.options[oid].name,
                        "price_delta": data.options[oid].price_delta,
                    }
                    for oid in item.option_ids
                ],
            }
        )
        totals.append(line)
        units += item.quantity * db_product.prep_units
    validation.validate_order_total_units(units)
    return lines, pricing.order_total(totals), units


async def _publish(bus: EventBus | None, channel: str, message: dict[str, Any]) -> None:
    if bus is not None:
        await bus.publish(channel, message)


async def create(
    session: AsyncSession,
    payload: OrderCreateIn,
    idempotency_key: str,
    bus: EventBus | None,
    now_utc: datetime,
) -> OrderCreateOut:
    key_hash = body_hash(canonical_payload(payload))

    existing = await repository.find_by_idempotency(session, idempotency_key)
    if existing is not None:
        if existing.idempotency_hash != key_hash:
            raise ValidationError(
                "idempotency_conflict", "Idempotency key reused with another body", {}
            )
        items = await repository.order_items(session, existing.id)
        return OrderCreateOut(order=order_out(existing, items), access_token=existing.access_token)

    data = await load_catalog(session, payload.location_id)
    loc = data.location
    lines, total, units = _price_lines(data, payload)
    if units > loc.slot_capacity:
        raise ValidationError("order_too_large", "Order exceeds slot capacity", {"units": units})
    slots = await get_slots(session, payload.location_id, units, now_utc)
    slot_start, is_asap = resolve_slot(loc, units, payload.mode, payload.pickup_at, slots)

    try:
        # Одна транзакция: резерв + счётчик + заказ. Блокировки строк сериализуют гонки.
        await repository.ensure_slot_row(session, loc.id, slot_start)
        row = await repository.get_slot_for_update(session, loc.id, slot_start)
        assert row is not None
        if row.units_reserved + units > loc.slot_capacity:
            raise ValidationError("slot_unavailable", "Slot just filled up", {})
        row.units_reserved += units

        tz: tzinfo
        try:
            tz = ZoneInfo(loc.timezone)
        except Exception:
            tz = UTC
        day = now_utc.astimezone(tz).date()
        n = await repository.next_order_number(session, loc.id, day)

        order = Order(
            code=f"{loc.code}-{n:03d}",
            location_id=loc.id,
            status=CONFIRMED,
            mode=payload.mode,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            comment=payload.comment or "",
            pickup_at=slot_start,
            is_asap=is_asap,
            units=units,
            total=total,
            currency=settings.default_currency,
            payment_method="cash_on_pickup",
            idempotency_key=idempotency_key,
            idempotency_hash=key_hash,
            access_token=new_access_token(),
        )
        session.add(order)
        await session.flush()
        for line in lines:
            session.add(OrderItem(order_id=order.id, **line))
        await repository.add_status_event(session, order.id, None, CONFIRMED, "customer")
        await session.commit()
    except IntegrityError as exc:
        # Гонка одинаковых Idempotency-Key: unique-constraint, перечитываем.
        await session.rollback()
        dup = await repository.find_by_idempotency(session, idempotency_key)
        if dup is not None:
            if dup.idempotency_hash != key_hash:
                raise ValidationError(
                    "idempotency_conflict", "Idempotency key reused with another body", {}
                ) from exc
            items = await repository.order_items(session, dup.id)
            return OrderCreateOut(order=order_out(dup, items), access_token=dup.access_token)
        raise
    except ValidationError:
        await session.rollback()
        raise

    items = await repository.order_items(session, order.id)
    out = OrderCreateOut(order=order_out(order, items), access_token=order.access_token)
    await _publish(bus, f"location:{loc.id}", {"type": "order_created", "order_id": order.id})
    await _publish(
        bus,
        f"order:{order.id}",
        {"type": "status", "order_id": order.id, "from": None, "to": CONFIRMED},
    )
    return out


async def get_guest_order(session: AsyncSession, order_id: int, token: str | None) -> Order:
    order = await repository.get_order(session, order_id)
    if order is None:
        raise ValidationError("not_found", "Order not found", {"order_id": order_id})
    if not token or not secrets_equal(order.access_token, token):
        raise ValidationError("unauthorized", "Invalid access token", {})
    return order


def secrets_equal(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a, b)


async def change_status(
    session: AsyncSession, order_id: int, to_status: str, actor: str, bus: EventBus | None
) -> Order:
    order = await repository.get_order_for_update(session, order_id)
    if order is None:
        raise ValidationError("not_found", "Order not found", {"order_id": order_id})
    allowed = TRANSITIONS.get(order.status, {})
    if to_status not in allowed or actor not in allowed[to_status]:
        raise ValidationError(
            "invalid_transition",
            f"Cannot move {order.status} -> {to_status} as {actor}",
            {"from": order.status, "to": to_status},
        )
    try:
        from_status = order.status
        order.status = to_status
        await repository.add_status_event(session, order.id, from_status, to_status, actor)
        if to_status == CANCELLED:
            # Освобождаем вместимость слота по снапшоту нагрузки заказа.
            row = await repository.get_slot_for_update(session, order.location_id, order.pickup_at)
            if row is not None:
                row.units_reserved = max(row.units_reserved - order.units, 0)
        await session.commit()
    except ValidationError:
        await session.rollback()
        raise

    await _publish(
        bus,
        f"order:{order.id}",
        {
            "type": "status",
            "order_id": order.id,
            "from": from_status,
            "to": to_status,
            "actor": actor,
        },
    )
    await _publish(
        bus, f"location:{order.location_id}", {"type": "order_updated", "order_id": order.id}
    )
    return order


async def cancel_by_customer(
    session: AsyncSession, order_id: int, token: str | None, bus: EventBus | None
) -> Order:
    await get_guest_order(session, order_id, token)
    return await change_status(session, order_id, CANCELLED, "customer", bus)


async def staff_orders(session: AsyncSession, location_id: int) -> list[Order]:
    return await repository.active_orders_for_location(session, location_id)


async def active_order_views(session: AsyncSession, location_id: int) -> list[OrderOut]:
    """Активные заказы точки со снапшотами позиций (для модуля staff)."""
    orders = await repository.active_orders_for_location(session, location_id)
    views: list[OrderOut] = []
    for order in orders:
        items = await repository.order_items(session, order.id)
        views.append(order_out(order, items))
    return views


async def full_order_view(session: AsyncSession, order_id: int) -> OrderOut:
    order = await repository.get_order(session, order_id)
    if order is None:
        raise ValidationError("not_found", "Order not found", {"order_id": order_id})
    items = await repository.order_items(session, order.id)
    return order_out(order, items)


async def guest_order_snapshot(
    session: AsyncSession, order_id: int, token: str | None
) -> dict[str, Any]:
    order = await get_guest_order(session, order_id, token)
    items = await repository.order_items(session, order.id)
    return order_out(order, items).model_dump(mode="json")


async def verify_order_location(session: AsyncSession, order_id: int, location_id: int) -> None:
    """Проверка принадлежности заказа точке (для модуля staff). Чужое — 404."""
    order = await repository.get_order(session, order_id)
    if order is None or order.location_id != location_id:
        raise ValidationError("not_found", "Order not found", {"order_id": order_id})
