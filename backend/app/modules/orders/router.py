from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import AppError
from app.core.sse import sse_response
from app.modules.menu.validation import ValidationError
from app.modules.orders import service
from app.modules.orders.schemas import (
    OrderCreateIn,
    OrderCreateOut,
    OrderOut,
    SlotsOut,
)

router = APIRouter(tags=["orders"])


def _err(exc: ValidationError) -> AppError:
    status = 404 if exc.code == "not_found" else 401 if exc.code == "unauthorized" else 400
    return AppError(exc.code, exc.message, status_code=status, details=exc.details)


def _bus(request: Request) -> Any:
    return request.app.state.bus


def _token(query_token: str | None, header_token: str | None) -> str | None:
    if query_token:
        return query_token
    if header_token and header_token.lower().startswith("bearer "):
        return header_token[7:]
    return header_token


@router.get("/locations/{location_id}/slots", response_model=SlotsOut)
async def _slots(
    location_id: int,
    units: int = Query(default=1, ge=1),
    session: AsyncSession = Depends(get_session),
) -> SlotsOut:
    try:
        return await service.get_slots(session, location_id, units, datetime.now(UTC))
    except ValidationError as exc:
        raise _err(exc) from exc


@router.post("/orders", response_model=OrderCreateOut, status_code=201)
async def _create_order(
    payload: OrderCreateIn,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
) -> OrderCreateOut:
    if not idempotency_key:
        raise AppError("validation_error", "Idempotency-Key header required", status_code=400)
    try:
        return await service.create(
            session, payload, idempotency_key, _bus(request), datetime.now(UTC)
        )
    except ValidationError as exc:
        raise _err(exc) from exc


@router.get("/orders/{order_id}", response_model=OrderOut)
async def _get_order(
    order_id: int,
    token: str | None = Query(default=None),
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    try:
        order = await service.get_guest_order(session, order_id, _token(token, x_access_token))
        return await service.full_order_view(session, order.id)
    except ValidationError as exc:
        raise _err(exc) from exc


@router.get("/orders/{order_id}/events")
async def _order_events(
    order_id: int,
    request: Request,
    token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    try:
        snapshot = await service.guest_order_snapshot(session, order_id, token)
    except ValidationError as exc:
        raise _err(exc) from exc
    return sse_response(_bus(request), f"order:{order_id}", {"type": "snapshot", "order": snapshot})


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
async def _cancel_order(
    order_id: int,
    request: Request,
    token: str | None = Query(default=None),
    x_access_token: str | None = Header(default=None, alias="X-Access-Token"),
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    try:
        order = await service.cancel_by_customer(
            session, order_id, _token(token, x_access_token), _bus(request)
        )
        return await service.full_order_view(session, order.id)
    except ValidationError as exc:
        raise _err(exc) from exc
