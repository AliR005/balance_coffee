"""Бонусы (SPEC 10.3): 1 балл = 1 рубль. Начисление 5% вниз при picked_up,
списание до 50% суммы, уровни по lifetime-тратам. Всё настраивается конфигом."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.bonus import repository
from app.modules.bonus.models import BonusAccount, BonusTransaction
from app.modules.bonus.schemas import AccountOut, LevelOut, TransactionOut
from app.modules.menu.validation import ValidationError

ACCRUAL = "accrual"
REDEEM = "redeem"
ADJUST = "adjust"


def accrual_for(paid_kopeks: int) -> int:
    """Баллы за оплаченную сумму: 5% вниз. Целочисленно, без float."""
    if paid_kopeks <= 0:
        return 0
    return paid_kopeks * settings.bonus_accrual_pct // 10_000


def redeem_for(balance: int, requested: int, total_kopeks: int) -> int:
    """Сколько баллов можно списать: баланс, запрос и 50% суммы."""
    cap = total_kopeks * settings.bonus_max_redeem_pct // 10_000
    return max(min(balance, requested, cap), 0)


def parse_levels() -> list[tuple[str, int]]:
    levels: list[tuple[str, int]] = []
    for part in settings.bonus_levels.split(","):
        name, _, threshold = part.partition(":")
        name, threshold = name.strip(), threshold.strip()
        if name and threshold.lstrip("-").isdigit():
            levels.append((name, int(threshold)))
    return sorted(levels, key=lambda x: x[1]) or [("Эспрессо", 0)]


def level_for(lifetime_kopeks: int) -> LevelOut:
    levels = parse_levels()
    current = levels[0]
    nxt: tuple[str, int] | None = None
    for i, (name, threshold) in enumerate(levels):
        if lifetime_kopeks >= threshold:
            current = (name, threshold)
            nxt = levels[i + 1] if i + 1 < len(levels) else None
        else:
            nxt = (name, threshold)
            break
    to_next = (nxt[1] - lifetime_kopeks) if nxt else 0
    return LevelOut(name=current[0], next_name=nxt[0] if nxt else None, to_next_kopeks=to_next)


def account_out(account: BonusAccount) -> AccountOut:
    return AccountOut(
        phone=account.phone,
        balance=account.balance,
        lifetime_spent=account.lifetime_spent,
        level=level_for(account.lifetime_spent),
    )


async def ensure_account(session: AsyncSession, phone: str, guest_token: str) -> BonusAccount:
    return await repository.ensure_account(session, phone, guest_token)


async def reserve_redeem(
    session: AsyncSession, phone: str, requested: int, lines_total: int, guest_token: str
) -> tuple[BonusAccount | None, int, int]:
    """Блокирует счёт, списывает баллы сразу (в транзакции заказа)."""
    if requested <= 0:
        return None, 0, 0
    account = await repository.get_account_for_update(session, phone)
    if account is None or account.balance <= 0:
        return None, 0, 0
    points = redeem_for(account.balance, requested, lines_total)
    if points <= 0:
        return account, 0, 0
    account.balance -= points
    account.guest_token = guest_token
    await session.flush()
    return account, points, points * 100


async def record_redeem(session: AsyncSession, account_id: int, points: int, order_id: int) -> None:
    if points <= 0:
        return
    session.add(
        BonusTransaction(account_id=account_id, type=REDEEM, amount=-points, order_id=order_id)
    )


async def accrue(
    session: AsyncSession, phone: str, paid_kopeks: int, order_id: int, guest_token: str
) -> int:
    """Начисление при picked_up. Повтор по тому же заказу не начисляет дважды."""
    if await repository.txn_for_order(session, order_id, ACCRUAL) is not None:
        return 0
    points = accrual_for(paid_kopeks)
    account = await repository.get_account_for_update(session, phone)
    if account is None:
        account = BonusAccount(phone=phone, balance=0, lifetime_spent=0, guest_token=guest_token)
        session.add(account)
        await session.flush()
    else:
        account.guest_token = guest_token
    if points > 0:
        account.balance += points
        session.add(
            BonusTransaction(account_id=account.id, type=ACCRUAL, amount=points, order_id=order_id)
        )
    account.lifetime_spent += paid_kopeks
    await session.flush()
    return points


async def refund(session: AsyncSession, order_id: int) -> None:
    """Возврат списанных баллов при отмене. Начислений при отмене нет (только picked_up)."""
    redeem = await repository.txn_for_order(session, order_id, REDEEM)
    if redeem is None or redeem.amount >= 0:
        return
    if await repository.txn_for_order(session, order_id, ADJUST) is not None:
        return
    account = await repository.get_account_by_id_for_update(session, redeem.account_id)
    if account is None:
        return
    points = -redeem.amount
    account.balance += points
    session.add(
        BonusTransaction(account_id=account.id, type=ADJUST, amount=points, order_id=order_id)
    )
    await session.flush()


async def get_account_view(session: AsyncSession, phone: str, token: str | None) -> AccountOut:
    account = await repository.get_account(session, phone)
    if account is None:
        return AccountOut(phone=phone, balance=0, lifetime_spent=0, level=level_for(0))
    if not token or token != account.guest_token:
        raise ValidationError("unauthorized", "Invalid bonus token", {})
    return account_out(account)


async def get_transactions(
    session: AsyncSession, phone: str, token: str | None
) -> list[TransactionOut]:
    account = await repository.get_account(session, phone)
    if account is None:
        return []
    if not token or token != account.guest_token:
        raise ValidationError("unauthorized", "Invalid bonus token", {})
    rows = await repository.transactions(session, account.id)
    return [
        TransactionOut(
            id=r.id, type=r.type, amount=r.amount, order_id=r.order_id, created_at=r.created_at
        )
        for r in rows
    ]
