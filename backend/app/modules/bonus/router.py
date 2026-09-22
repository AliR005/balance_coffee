from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import AppError
from app.modules.bonus import service
from app.modules.bonus.schemas import AccountOut, TransactionOut
from app.modules.menu.validation import ValidationError

router = APIRouter(prefix="/bonus", tags=["bonus"])


def _err(exc: ValidationError) -> AppError:
    status = 401 if exc.code == "unauthorized" else 400
    return AppError(exc.code, exc.message, status_code=status, details=exc.details)


@router.get("/account", response_model=AccountOut)
async def _account(
    phone: str = Query(min_length=5, max_length=32),
    token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> AccountOut:
    try:
        return await service.get_account_view(session, phone, token)
    except ValidationError as exc:
        raise _err(exc) from exc


@router.get("/transactions", response_model=list[TransactionOut])
async def _transactions(
    phone: str = Query(min_length=5, max_length=32),
    token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[TransactionOut]:
    try:
        return await service.get_transactions(session, phone, token)
    except ValidationError as exc:
        raise _err(exc) from exc
