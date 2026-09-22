"""Гонка за слот: N параллельных POST на вместимость M. Реальный gather на настоящей БД."""

import asyncio
import uuid

from tests.helpers05 import create_order, locations, menu_by_slug, order_body, size_s

ROUNDS = 20  # итого 20 исполнений гонки для стабильности


async def _round(race_client, tv: dict, slot_start: str, tag: str) -> None:  # type: ignore[no-untyped-def]
    menu = await menu_by_slug(race_client, tv["id"])
    esp = menu["espresso"]
    item = {"product_id": esp["id"], "option_ids": [size_s(esp)], "quantity": 1}
    body = order_body(tv["id"], [item], mode="scheduled", pickup_at=slot_start)

    async def one(i: int):  # type: ignore[no-untyped-def]
        return await create_order(race_client, body, key=f"race-{tag}-{i}")

    results = await asyncio.gather(*[one(i) for i in range(10)])
    ok = [r for r in results if r.status_code == 201]
    busy = [r for r in results if r.status_code == 400 and r.json()["code"] == "slot_unavailable"]
    assert len(ok) == 4, [r.status_code for r in results]
    assert len(busy) == 6, [r.json() for r in results if r.status_code != 201]
    # Отменяем созданные, чтобы освободить слот следующим проверкам.
    for r in ok:
        order = r.json()["order"]
        cancel = await race_client.post(
            f"/orders/{order['id']}/cancel", params={"token": r.json()["access_token"]}
        )
        assert cancel.status_code == 200, cancel.text


async def test_slot_race_stable_20_rounds(race_client) -> None:  # type: ignore[no-untyped-def]
    import pytest as _pytest

    locs = await locations(race_client)
    pt = locs["PT"]  # capacity 4: ровно 4 успеха из 10
    slots = (await race_client.get(f"/locations/{pt['id']}/slots", params={"units": 1})).json()
    # Только пустые слоты (remaining == capacity), иначе точный счёт 4/6 невозможен.
    empty = [s["start"] for s in slots["slots"] if s["remaining"] == 4]
    if len(empty) < ROUNDS:
        _pytest.skip("not enough empty slots — reset dev DB (make reset-demo в фазе 09)")
    run = uuid.uuid4().hex[:8]
    for n in range(ROUNDS):
        await _round(race_client, pt, empty[n], f"{run}-r{n}")
