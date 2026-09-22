import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.ratelimit as ratelimit
from app.core.config import settings
from app.core.db import get_session
from app.main import create_app

# Сьют создаёт сотни заказов с одного IP за секунды — продовый лимит 60/мин
# здесь неуместен; сам лимитер покрыт отдельным тестом.
ratelimit.LIMITS["/orders"] = (10_000, 60)


@pytest.fixture(scope="session", autouse=True)
async def _reset_dev_state():  # type: ignore[no-untyped-def]
    """Тесты пишут в dev-БД: перед сьютом возвращаем seed-состояние (меню, стоп-лист)
    и отменяем висящие активные заказы прошлых прогонов, чтобы освободить слоты."""
    try:
        import importlib.util
        from pathlib import Path

        spec = importlib.util.spec_from_file_location("seed_mod", Path("scripts") / "seed.py")
        assert spec and spec.loader
        seed_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_mod)
        await seed_mod.main()

        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        app = create_app()

        async def _override():  # type: ignore[no-untyped-def]
            async with factory() as session:
                yield session

        app.dependency_overrides[get_session] = _override
        transport = httpx.ASGITransport(app=app)
        pins = {"TV": "1234", "PT": "4321"}
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            locs = (await client.get("/locations")).json()
            for loc in locs:
                pin = pins.get(loc["code"])
                if pin is None:
                    continue
                login = await client.post(
                    "/staff/login", json={"location_id": loc["id"], "pin": pin}
                )
                if login.status_code != 200:
                    continue
                headers = {"Authorization": f"Bearer {login.json()['token']}"}
                orders = (await client.get("/staff/orders", headers=headers)).json()
                for order in orders:
                    await client.post(
                        f"/staff/orders/{order['id']}/status",
                        json={"to_status": "cancelled"},
                        headers=headers,
                    )
        await engine.dispose()
    except Exception:
        pass  # БД недоступна — тесты сами пропустятся


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


@pytest.fixture()
async def race_client():  # type: ignore[no-untyped-def]
    """Клиент с отдельной сессией на запрос — для настоящих параллельных гонок."""
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as probe:
            from sqlalchemy import text as _text

            await probe.execute(_text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"db unavailable: {exc}")
    app = create_app()

    async def _override():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    await engine.dispose()
