import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import get_session
from app.main import create_app


@pytest.fixture()
async def db_session() -> AsyncSession:  # type: ignore[misc]
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as session:
            yield session  # type: ignore[misc]
        await engine.dispose()
    except Exception as exc:
        pytest.skip(f"db unavailable: {exc}")


@pytest.fixture()
async def api_client(db_session: AsyncSession):  # type: ignore[no-untyped-def]
    app = create_app()

    async def _override():  # type: ignore[no-untyped-def]
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
