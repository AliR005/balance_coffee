"""Шина событий за Protocol. В MVP — в памяти процесса (один воркер).
Redis подставится без правок сервисов: достаточно другой реализации EventBus."""

import asyncio
from typing import Any, Protocol


class EventBus(Protocol):
    async def publish(self, channel: str, message: dict[str, Any]) -> None: ...

    def subscribe(self, channel: str) -> Any: ...


class InMemoryEventBus:
    """Каналы `order:{id}` (статус одного заказа) и `location:{id}` (доска баристы)."""

    def __init__(self, maxsize: int = 100) -> None:
        self._subs: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}
        self._maxsize = maxsize

    async def publish(self, channel: str, message: dict[str, Any]) -> None:
        for q in list(self._subs.get(channel, ())):
            if not q.full():
                q.put_nowait(message)

    async def _listen(self, channel: str, queue: asyncio.Queue[dict[str, Any]]):  # type: ignore[no-untyped-def]
        try:
            while True:
                yield await queue.get()
        finally:
            subs = self._subs.get(channel)
            if subs is not None:
                subs.discard(queue)

    def subscribe(self, channel: str):  # type: ignore[no-untyped-def]
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self._maxsize)
        self._subs.setdefault(channel, set()).add(queue)
        return self._listen(channel, queue)
