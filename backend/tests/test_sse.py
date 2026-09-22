"""SSE: подписчик получает снапшот и смену статуса.

httpx ASGITransport буферизует тело до more_body=False, поэтому бесконечные
SSE-потоки через него не тестируются — едем напрямую через raw ASGI.
"""

import asyncio
import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import get_session
from app.main import create_app
from tests.helpers05 import (
    create_order,
    latte_item,
    locations,
    menu_by_slug,
    order_body,
    staff_headers,
    staff_login,
)


@pytest.fixture()
async def sse_env():  # type: ignore[no-untyped-def]
    """App с сессией на запрос + httpx-клиент к нему же (для действий)."""
    import httpx

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
        yield app, client
    app.dependency_overrides.clear()
    await engine.dispose()


class StreamReader:
    """Минимальный SSE-клиент поверх raw ASGI."""

    def __init__(
        self, app, path: str, query: str = "", headers: list[tuple[bytes, bytes]] | None = None
    ):  # type: ignore[no-untyped-def]
        self.app = app
        self.scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": query.encode(),
            "headers": headers or [(b"host", b"test")],
            "server": ("test", 80),
            "client": ("testclient", 50000),
        }
        self.status: int | None = None
        self.chunks: list[bytes] = []
        self._done = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def _receive(self):  # type: ignore[no-untyped-def]
        if not hasattr(self, "_requested"):
            self._requested = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await self._done.wait()
        return {"type": "http.disconnect"}

    async def _send(self, msg):  # type: ignore[no-untyped-def]
        if msg["type"] == "http.response.start":
            self.status = msg["status"]
        elif msg["type"] == "http.response.body":
            if msg.get("body"):
                self.chunks.append(msg["body"])

    async def start(self) -> None:
        self._task = asyncio.create_task(self.app(self.scope, self._receive, self._send))

    async def wait_chunks(self, n: int, timeout: float = 10) -> list[bytes]:
        async with asyncio.timeout(timeout):
            while len(self.chunks) < n:
                await asyncio.sleep(0.02)
        return self.chunks

    async def stop(self) -> None:
        self._done.set()
        if self._task is not None:
            await asyncio.wait_for(asyncio.shield(self._task), timeout=10)


def sse_messages(chunks: list[bytes]) -> list[dict]:
    out = []
    for raw in b"".join(chunks).decode().split("\n\n"):
        for line in raw.splitlines():
            if line.startswith("data: "):
                out.append(json.loads(line[6:]))
    return out


async def test_order_events_flow(sse_env) -> None:  # type: ignore[no-untyped-def]
    app, client = sse_env
    locs = await locations(client)
    tv = locs["TV"]
    menu = await menu_by_slug(client, tv["id"])
    created = await create_order(client, order_body(tv["id"], [latte_item(menu)]))
    assert created.status_code == 201, created.text
    oid = created.json()["order"]["id"]
    guest = created.json()["access_token"]
    staff = staff_headers(await staff_login(client, tv["id"], "1234"))

    reader = StreamReader(app, f"/orders/{oid}/events", query=f"token={guest}")
    await reader.start()
    await reader.wait_chunks(1)
    assert reader.status == 200

    resp = await client.post(
        f"/staff/orders/{oid}/status", json={"to_status": "preparing"}, headers=staff
    )
    assert resp.status_code == 200
    await reader.wait_chunks(2)
    await reader.stop()

    msgs = sse_messages(reader.chunks)
    assert msgs[0]["type"] == "snapshot"
    assert msgs[0]["order"]["id"] == oid
    status_msgs = [m for m in msgs[1:] if m.get("type") == "status"]
    assert any(m.get("to") == "preparing" for m in status_msgs), msgs


async def test_order_events_require_token(sse_env) -> None:  # type: ignore[no-untyped-def]
    app, client = sse_env
    locs = await locations(client)
    tv = locs["TV"]
    menu = await menu_by_slug(client, tv["id"])
    created = await create_order(client, order_body(tv["id"], [latte_item(menu)]))
    oid = created.json()["order"]["id"]

    reader = StreamReader(app, f"/orders/{oid}/events")
    await reader.start()
    await reader.wait_chunks(1)
    await reader.stop()
    assert reader.status == 401


async def test_staff_stream_snapshot(sse_env) -> None:  # type: ignore[no-untyped-def]
    app, client = sse_env
    locs = await locations(client)
    tv = locs["TV"]
    token = await staff_login(client, tv["id"], "1234")

    reader = StreamReader(
        app, "/staff/orders/stream", query=f"token={token}", headers=[(b"host", b"test")]
    )
    await reader.start()
    await reader.wait_chunks(1)
    await reader.stop()
    assert reader.status == 200
    msgs = sse_messages(reader.chunks)
    assert msgs[0]["type"] == "snapshot"
    assert msgs[0]["location_id"] == tv["id"]
