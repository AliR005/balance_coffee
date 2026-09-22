"""Токены и PIN. Без новых зависимостей: HMAC из hashlib."""

import hashlib
import hmac
import secrets
import time

from app.core.config import settings


def new_access_token() -> str:
    """Гостевой токен заказа: 32 байта энтропии (SPEC 5.7)."""
    return secrets.token_urlsafe(32)


def hash_pin(pin: str) -> str:
    return "sha256:" + hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin: str, pin_hash: str | None) -> bool:
    if not pin_hash:
        return False
    return hmac.compare_digest(hash_pin(pin), pin_hash)


def mint_staff_token(location_id: int, ttl_hours: int | None = None) -> str:
    exp = (
        int(time.time())
        + (ttl_hours if ttl_hours is not None else settings.staff_token_ttl_hours) * 3600
    )
    body = f"{location_id}:{exp}"
    sig = hmac.new(settings.staff_token_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}:{sig}"


def verify_staff_token(token: str) -> int | None:
    """Возвращает location_id или None."""
    try:
        location_s, exp_s, sig = token.split(":")
        body = f"{location_s}:{exp_s}"
        want = hmac.new(
            settings.staff_token_secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(want, sig):
            return None
        if int(exp_s) < int(time.time()):
            return None
        return int(location_s)
    except (ValueError, TypeError):
        return None


def body_hash(canonical: str) -> str:
    return hashlib.sha256(canonical.encode()).hexdigest()
