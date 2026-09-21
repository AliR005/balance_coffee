from datetime import UTC
from datetime import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import AppError
from app.modules.menu import service
from app.modules.menu.schemas import LocationOut, MenuOut, QuoteIn, QuoteOut
from app.modules.menu.validation import ValidationError

router = APIRouter(prefix="/locations", tags=["locations"])


def _to_app_error(exc: ValidationError) -> AppError:
    status = 404 if exc.code == "not_found" else 400
    return AppError(exc.code, exc.message, status_code=status, details=exc.details)


@router.get("", response_model=list[LocationOut])
async def _list_locations(
    session: AsyncSession = Depends(get_session),
) -> list[LocationOut]:
    return await service.get_locations(session, dt.now(UTC))


@router.get("/{location_id}/menu", response_model=MenuOut)
async def _get_menu(location_id: int, session: AsyncSession = Depends(get_session)) -> MenuOut:
    try:
        return await service.get_menu(session, location_id)
    except ValidationError as exc:
        raise _to_app_error(exc) from exc


@router.post("/{location_id}/quote", response_model=QuoteOut)
async def _quote(
    location_id: int, payload: QuoteIn, session: AsyncSession = Depends(get_session)
) -> QuoteOut:
    try:
        return await service.quote(session, location_id, payload)
    except ValidationError as exc:
        raise _to_app_error(exc) from exc
