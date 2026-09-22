"""Staff: вход по PIN, заказы точки, стоп-лист. Делегирует orders/menu через их service."""

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.eventbus import EventBus
from app.core.security import mint_staff_token, verify_pin, verify_staff_token
from app.modules.menu.service import fetch_location, load_catalog, set_availability
from app.modules.menu.validation import ValidationError
from app.modules.orders import service as orders_service
from app.modules.orders.schemas import OrderOut
from app.modules.staff.schemas import (
    AvailabilityOut,
    LoginOut,
    OptionAvailabilityOut,
    ProductAvailabilityOut,
)

# Ограничение попыток входа: in-memory (сбрасывается при рестарте; в проде — Redis).
# Превышение отвечаем 401, как неверный PIN, чтобы не выдавать факт лимита.
_LOGIN_ATTEMPTS: dict[str, tuple[int, float]] = {}
LOGIN_MAX_ATTEMPTS = 10
LOGIN_WINDOW_SEC = 300


def _check_rate_limit(key: str) -> bool:
    now = time.time()
    count, reset = _LOGIN_ATTEMPTS.get(key, (0, now + LOGIN_WINDOW_SEC))
    if now > reset:
        count, reset = 0, now + LOGIN_WINDOW_SEC
    if count >= LOGIN_MAX_ATTEMPTS:
        return False
    _LOGIN_ATTEMPTS[key] = (count + 1, reset)
    return True


async def login(session: AsyncSession, location_id: int, pin: str, client_key: str) -> LoginOut:
    if not _check_rate_limit(f"{location_id}:{client_key}"):
        raise ValidationError("unauthorized", "Invalid PIN", {})
    try:
        loc = await fetch_location(session, location_id)
    except ValidationError:
        raise ValidationError("unauthorized", "Invalid PIN", {}) from None
    if not verify_pin(pin, loc.staff_pin_hash):
        raise ValidationError("unauthorized", "Invalid PIN", {})
    from app.core.config import settings

    ttl = settings.staff_token_ttl_hours
    return LoginOut(
        token=mint_staff_token(location_id, ttl),
        location_id=location_id,
        expires_at=int(time.time()) + ttl * 3600,
    )


def auth_location_id(token: str | None) -> int:
    location_id = verify_staff_token(token or "")
    if location_id is None:
        raise ValidationError("unauthorized", "Invalid staff token", {})
    return location_id


async def get_orders(session: AsyncSession, location_id: int) -> list[OrderOut]:
    await fetch_location(session, location_id)
    return await orders_service.active_order_views(session, location_id)


async def change_order_status(
    session: AsyncSession, location_id: int, order_id: int, to_status: str, bus: EventBus | None
) -> OrderOut:
    await orders_service.verify_order_location(session, order_id, location_id)
    updated = await orders_service.change_status(session, order_id, to_status, "staff", bus)
    return await orders_service.full_order_view(session, updated.id)


async def get_availability(session: AsyncSession, location_id: int) -> AvailabilityOut:
    data = await load_catalog(session, location_id)
    unavailable_options: set[int] = set()
    for prod in data.catalog.values():
        unavailable_options |= prod.unavailable_option_ids
    products = [
        ProductAvailabilityOut(id=p.id, name=p.name, available=data.catalog[p.id].available)
        for p in data.products.values()
    ]
    options = [
        OptionAvailabilityOut(
            id=o.id,
            name=o.name,
            group=data.groups[o.group_id].key,
            available=o.id not in unavailable_options,
        )
        for o in data.options.values()
    ]
    return AvailabilityOut(
        location_id=location_id,
        products=sorted(products, key=lambda p: p.id),
        options=sorted(options, key=lambda o: o.id),
    )


async def set_product(
    session: AsyncSession, location_id: int, product_id: int, is_available: bool
) -> None:
    data = await load_catalog(session, location_id)
    if product_id not in data.products:
        raise ValidationError("not_found", "Product not found", {"product_id": product_id})
    await set_availability(session, location_id, product_id, None, is_available)


async def set_option(
    session: AsyncSession, location_id: int, option_id: int, is_available: bool
) -> None:
    data = await load_catalog(session, location_id)
    if option_id not in data.options:
        raise ValidationError("not_found", "Option not found", {"option_id": option_id})
    await set_availability(session, location_id, None, option_id, is_available)
