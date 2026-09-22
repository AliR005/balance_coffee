import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import create_app


async def test_health() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert "X-Request-Id" in resp.headers


async def test_db_connection(db_session: AsyncSession) -> None:
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1
