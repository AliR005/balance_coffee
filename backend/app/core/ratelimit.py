"""Простой in-memory rate limit (один воркер; в проде с репликами — Redis/waf).
Применяется к POST /orders. /staff/login ограничен отдельно (см. staff.service)."""

import time

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.errors import error_payload

# path-prefix -> (лимит, окно_сек). Тесты поднимают лимит через этот словарь;
# продовое значение по умолчанию — 60 POST /orders в минуту с одного IP.
LIMITS: dict[str, tuple[int, int]] = {
    "/orders": (60, 60),
}

_hits: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    if request.method == "POST":
        for prefix, (limit, window) in LIMITS.items():
            path = request.url.path
            if path == prefix or path.startswith(prefix + "/"):
                key = f"{prefix}:{_client_ip(request)}"
                now = time.time()
                hits = [t for t in _hits.get(key, []) if now - t < window]
                if len(hits) >= limit:
                    return JSONResponse(
                        status_code=429,
                        content=error_payload("rate_limited", "Too many requests", {}),
                    )
                hits.append(now)
                _hits[key] = hits
                break
    return await call_next(request)
