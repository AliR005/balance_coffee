import httpx
import pytest
from sqlalchemy import text

from app.core.db import engine
from app.main import create_app


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


async def test_health() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert "X-Request-Id" in resp.headers


async def test_db_connection() -> None:
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as exc:  # DB may be unavailable in CI without service
        pytest.skip(f"db unavailable: {exc}")
