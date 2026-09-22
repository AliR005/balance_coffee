"""Бонусы: начисление, списание, возврат, уровни, гонка за баланс."""

import asyncio
import uuid

from app.modules.bonus.service import accrual_for, level_for, redeem_for
from tests.helpers05 import (
    create_order,
    espresso_item,
    latte_item,
    locations,
    menu_by_slug,
    order_body,
    staff_headers,
    staff_login,
)


def _phone() -> str:
    return f"+79{uuid.uuid4().hex[:9]}"


async def _drive_to_picked_up(client, oid: int, location_id: int, pin: str) -> None:  # type: ignore[no-untyped-def]
    headers = staff_headers(await staff_login(client, location_id, pin))
    for nxt in ("preparing", "ready", "picked_up"):
        resp = await client.post(
            f"/staff/orders/{oid}/status", json={"to_status": nxt}, headers=headers
        )
        assert resp.status_code == 200, resp.text


async def _account(client, phone: str, token: str):  # type: ignore[no-untyped-def]
    resp = await client.get("/bonus/account", params={"phone": phone, "token": token})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_math_floor_and_caps() -> None:
    assert accrual_for(32000) == 16
    assert accrual_for(19000) == 9
    assert accrual_for(0) == 0
    # Не больше баланса, запроса и 50% суммы.
    assert redeem_for(1000, 500, 32000) == 160  # 50% от 320₽
    assert redeem_for(100, 500, 32000) == 100
    assert redeem_for(1000, 50, 32000) == 50
    assert redeem_for(1000, 500, 0) == 0


def test_levels_boundaries() -> None:
    assert level_for(0).name == "Эспрессо"
    assert level_for(499_999).name == "Эспрессо"
    assert level_for(500_000).name == "Латте"
    assert level_for(1_499_999).name == "Латте"
    assert level_for(1_500_000).name == "Баланс"
    assert level_for(500_000).to_next_kopeks == 1_000_000


async def test_accrue_on_picked_up(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    phone = _phone()
    created = await create_order(
        api_client, order_body(tv["id"], [latte_item(menu)], customer_phone=phone)
    )
    assert created.status_code == 201, created.text
    oid = created.json()["order"]["id"]
    token = created.json()["access_token"]
    total = created.json()["order"]["total"]

    await _drive_to_picked_up(api_client, oid, tv["id"], "1234")
    acc = await _account(api_client, phone, token)
    assert acc["balance"] == total * 5 // 10_000
    assert acc["lifetime_spent"] == total
    assert acc["level"]["name"] == "Эспрессо"

    txns = (
        await api_client.get("/bonus/transactions", params={"phone": phone, "token": token})
    ).json()
    assert [t["type"] for t in txns] == ["accrual"]
    assert txns[0]["amount"] == total * 5 // 10_000


async def test_no_double_accrue(api_client, db_session) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy import select

    from app.modules.bonus.models import BonusTransaction

    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    phone = _phone()
    created = await create_order(
        api_client, order_body(tv["id"], [latte_item(menu)], customer_phone=phone)
    )
    oid = created.json()["order"]["id"]
    await _drive_to_picked_up(api_client, oid, tv["id"], "1234")
    # Повторный picked_up невозможен (терминал), но прямой вызов accrue идемпотентен.
    from app.modules.bonus import service as bonus_service

    again = await bonus_service.accrue(db_session, phone, 32000, oid, "tok")
    assert again == 0
    rows = (
        (await db_session.execute(select(BonusTransaction).where(BonusTransaction.order_id == oid)))
        .scalars()
        .all()
    )
    assert len([r for r in rows if r.type == "accrual"]) == 1


async def test_redeem_flow_and_refund(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    phone = _phone()

    # Первый заказ 32000-3000=29000? латте M: (34000)*1 → копим 17 баллов... считаем точно.
    first = await create_order(
        api_client, order_body(tv["id"], [latte_item(menu)], customer_phone=phone)
    )
    assert first.status_code == 201, first.text
    foid = first.json()["order"]["id"]
    ftotal = first.json()["order"]["total"]
    await _drive_to_picked_up(api_client, foid, tv["id"], "1234")
    earned = ftotal * 5 // 10_000
    assert earned > 0
    ftoken = first.json()["access_token"]

    # Второй заказ со списанием всего заработанного.
    second = await create_order(
        api_client,
        order_body(tv["id"], [latte_item(menu)], customer_phone=phone, use_bonus_points=earned),
    )
    assert second.status_code == 201, second.text
    sorder = second.json()["order"]
    assert sorder["bonus_applied"] == earned * 100
    assert sorder["total"] == ftotal - earned * 100
    stoken = second.json()["access_token"]

    acc = await _account(api_client, phone, stoken)
    assert acc["balance"] == 0

    # Отмена возвращает списанное и не начисляет.
    cancel = await api_client.post(f"/orders/{sorder['id']}/cancel", params={"token": stoken})
    assert cancel.status_code == 200
    acc2 = await _account(api_client, phone, stoken)
    assert acc2["balance"] == earned
    txns = (
        await api_client.get("/bonus/transactions", params={"phone": phone, "token": stoken})
    ).json()
    assert sorted(t["type"] for t in txns) == ["accrual", "adjust", "redeem"]
    # Токен привязан к последнему заказу: старый уже не подходит.
    old = await api_client.get("/bonus/account", params={"phone": phone, "token": ftoken})
    assert old.status_code == 401


async def test_redeem_capped_by_half(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    phone = _phone()
    # Копи́м баланс маленькими заказами: латте 31000 → 15 баллов × 3 = 45.
    for _ in range(3):
        o = await create_order(
            api_client, order_body(tv["id"], [latte_item(menu)], customer_phone=phone)
        )
        await _drive_to_picked_up(api_client, o.json()["order"]["id"], tv["id"], "1234")
    big = await create_order(
        api_client,
        order_body(tv["id"], [espresso_item(menu)], customer_phone=phone, use_bonus_points=10**9),
    )
    assert big.status_code == 201, big.text
    # Эспрессо S: 19000 → cap 50% = 95, но баланс 45 — побеждает баланс.
    assert big.json()["order"]["bonus_applied"] == 4500
    assert big.json()["order"]["total"] == 19000 - 4500


async def test_redeem_race_no_negative(race_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(race_client)
    tv = locs["TV"]
    menu = await menu_by_slug(race_client, tv["id"])
    phone = _phone()
    first = await create_order(
        race_client, order_body(tv["id"], [latte_item(menu)], customer_phone=phone)
    )
    await _drive_to_picked_up(race_client, first.json()["order"]["id"], tv["id"], "1234")
    earned = first.json()["order"]["total"] * 5 // 10_000

    # Гонка на пустом слоте (scheduled), чтобы счёт был детерминирован.
    import pytest as _pytest

    slots = (await race_client.get(f"/locations/{tv['id']}/slots", params={"units": 1})).json()
    empty = [s["start"] for s in slots["slots"] if s["remaining"] == 6]
    if not empty:
        _pytest.skip("no empty TV slot")
    slot_start = empty[0]

    async def one(i: int):  # type: ignore[no-untyped-def]
        return await create_order(
            race_client,
            order_body(
                tv["id"],
                [espresso_item(menu)],
                customer_phone=phone,
                use_bonus_points=earned,
                mode="scheduled",
                pickup_at=slot_start,
            ),
            key=f"bonus-race-{uuid.uuid4().hex[:8]}-{i}",
        )

    results = await asyncio.gather(*[one(i) for i in range(4)])
    assert all(r.status_code == 201 for r in results), [r.text for r in results]
    spent = sum(r.json()["order"]["bonus_applied"] // 100 for r in results)
    assert spent <= earned, (spent, earned)

    # Токен привязан к последнему закоммиченному заказу (порядок завершения ≠ порядок
    # коммитов) — перебираем с конца, пока один не подойдёт.
    acc = None
    for r in reversed(results):
        resp = await race_client.get(
            "/bonus/account", params={"phone": phone, "token": r.json()["access_token"]}
        )
        if resp.status_code == 200:
            acc = resp.json()
            break
    assert acc is not None
    assert acc["balance"] >= 0


async def test_bonus_auth(api_client) -> None:  # type: ignore[no-untyped-def]
    assert (
        await api_client.get("/bonus/account", params={"phone": "+70000000000"})
    ).status_code == 200
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    phone = _phone()
    created = await create_order(
        api_client, order_body(tv["id"], [latte_item(menu)], customer_phone=phone)
    )
    token = created.json()["access_token"]
    assert (
        await api_client.get("/bonus/account", params={"phone": phone, "token": "wrong"})
    ).status_code == 401
    assert (
        await api_client.get("/bonus/account", params={"phone": phone, "token": token})
    ).status_code == 200
