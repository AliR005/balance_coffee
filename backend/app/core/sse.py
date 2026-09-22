"""SSE-потоки: снапшот при подключении, события шины, keepalive. Фронт переподключается сам."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi.responses import StreamingResponse

from app.core.eventbus import EventBus


async def event_stream(bus: EventBus, channel: str, snapshot: dict[str, Any]) -> AsyncIterator[str]:
    yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"
    sub = bus.subscribe(channel)
    try:
        while True:
            try:
                msg = await asyncio.wait_for(sub.__anext__(), timeout=15)
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            except StopAsyncIteration:
                break
            except TimeoutError:
                yield ": ping\n\n"
    finally:
        await sub.aclose()


def sse_response(bus: EventBus, channel: str, snapshot: dict[str, Any]) -> StreamingResponse:
    return StreamingResponse(
        event_stream(bus, channel, snapshot),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
