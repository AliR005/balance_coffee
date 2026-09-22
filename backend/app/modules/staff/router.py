from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import AppError
from app.core.sse import sse_response
from app.modules.menu.validation import ValidationError
from app.modules.orders.schemas import OrderOut, StatusChangeIn
from app.modules.staff import service
from app.modules.staff.schemas import (
    AvailabilityOut,
    AvailabilityUpdateIn,
    LoginIn,
    LoginOut,
)

router = APIRouter(prefix="/staff", tags=["staff"])


def _err(exc: ValidationError) -> AppError:
    status = 404 if exc.code == "not_found" else 401 if exc.code == "unauthorized" else 400
    return AppError(exc.code, exc.message, status_code=status, details=exc.details)


def _bus(request: Request) -> Any:
    return request.app.state.bus


def _staff_token(authorization: str | None, query_token: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    return query_token


async def _auth(
    request: Request,
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> int:
    try:
        return service.auth_location_id(_staff_token(authorization, token))
    except ValidationError as exc:
        raise _err(exc) from exc


@router.post("/login", response_model=LoginOut)
async def _login(
    payload: LoginIn, request: Request, session: AsyncSession = Depends(get_session)
) -> LoginOut:
    client_key = request.client.host if request.client else "unknown"
    try:
        return await service.login(session, payload.location_id, payload.pin, client_key)
    except ValidationError as exc:
        raise _err(exc) from exc


@router.get("/orders", response_model=list[OrderOut])
async def _orders(
    location_id: int = Depends(_auth), session: AsyncSession = Depends(get_session)
) -> list[OrderOut]:
    try:
        return await service.get_orders(session, location_id)
    except ValidationError as exc:
        raise _err(exc) from exc


@router.get("/orders/stream")
async def _orders_stream(request: Request, location_id: int = Depends(_auth)):  # type: ignore[no-untyped-def]
    return sse_response(
        _bus(request), f"location:{location_id}", {"type": "snapshot", "location_id": location_id}
    )


@router.post("/orders/{order_id}/status", response_model=OrderOut)
async def _change_status(
    order_id: int,
    payload: StatusChangeIn,
    request: Request,
    location_id: int = Depends(_auth),
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    try:
        return await service.change_order_status(
            session, location_id, order_id, payload.to_status, _bus(request)
        )
    except ValidationError as exc:
        raise _err(exc) from exc


@router.get("/availability", response_model=AvailabilityOut)
async def _availability(
    location_id: int = Depends(_auth), session: AsyncSession = Depends(get_session)
) -> AvailabilityOut:
    try:
        return await service.get_availability(session, location_id)
    except ValidationError as exc:
        raise _err(exc) from exc


@router.put("/availability/products/{product_id}")
async def _product_availability(
    product_id: int,
    payload: AvailabilityUpdateIn,
    location_id: int = Depends(_auth),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    try:
        await service.set_product(session, location_id, product_id, payload.is_available)
        return {"ok": True}
    except ValidationError as exc:
        raise _err(exc) from exc


@router.put("/availability/options/{option_id}")
async def _option_availability(
    option_id: int,
    payload: AvailabilityUpdateIn,
    location_id: int = Depends(_auth),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    try:
        await service.set_option(session, location_id, option_id, payload.is_available)
        return {"ok": True}
    except ValidationError as exc:
        raise _err(exc) from exc
