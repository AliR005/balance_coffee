"""Статусы: переходы, права, отмена с освобождением слота, события."""

from sqlalchemy import select

from app.modules.orders.models import OrderStatusEvent
from tests.helpers05 import (
    create_order,
    espresso_item,
    locations,
    menu_by_slug,
    order_body,
    staff_headers,
    staff_login,
)


async def test_full_lifecycle_staff(api_client, db_session) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    created = await create_order(api_client, order_body(tv["id"], [espresso_item(menu)]))
    oid = created.json()["order"]["id"]
    token = await staff_login(api_client, tv["id"], "1234")
    headers = staff_headers(token)

    for nxt in ("preparing", "ready", "picked_up"):
        resp = await api_client.post(
            f"/staff/orders/{oid}/status", json={"to_status": nxt}, headers=headers
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == nxt

    events = (
        (await db_session.execute(select(OrderStatusEvent).where(OrderStatusEvent.order_id == oid)))
        .scalars()
        .all()
    )
    assert [(e.from_status, e.to_status, e.actor) for e in events] == [
        (None, "confirmed", "customer"),
        ("confirmed", "preparing", "staff"),
        ("preparing", "ready", "staff"),
        ("ready", "picked_up", "staff"),
    ]


async def test_invalid_transitions(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    created = await create_order(api_client, order_body(tv["id"], [espresso_item(menu)]))
    oid = created.json()["order"]["id"]
    token = await staff_login(api_client, tv["id"], "1234")
    headers = staff_headers(token)

    # confirmed -> ready запрещён
    resp = await api_client.post(
        f"/staff/orders/{oid}/status", json={"to_status": "ready"}, headers=headers
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_transition"
    # Неизвестный статус
    resp = await api_client.post(
        f"/staff/orders/{oid}/status", json={"to_status": "flying"}, headers=headers
    )
    assert resp.status_code == 400


async def test_customer_cancel_only_when_confirmed(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    created = await create_order(api_client, order_body(tv["id"], [espresso_item(menu)]))
    oid = created.json()["order"]["id"]
    guest = created.json()["access_token"]
    staff = staff_headers(await staff_login(api_client, tv["id"], "1234"))

    # Гость отменяет confirmed — можно.
    resp = await api_client.post(f"/orders/{oid}/cancel", params={"token": guest})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # Второй заказ доводим до preparing — гость уже не может.
    created2 = await create_order(api_client, order_body(tv["id"], [espresso_item(menu)]))
    oid2 = created2.json()["order"]["id"]
    guest2 = created2.json()["access_token"]
    await api_client.post(
        f"/staff/orders/{oid2}/status", json={"to_status": "preparing"}, headers=staff
    )
    resp = await api_client.post(f"/orders/{oid2}/cancel", params={"token": guest2})
    assert resp.status_code == 400
    assert resp.json()["code"] == "invalid_transition"
    # А staff preparing отменить может.
    resp = await api_client.post(
        f"/staff/orders/{oid2}/status", json={"to_status": "cancelled"}, headers=staff
    )
    assert resp.status_code == 200


async def test_cancel_frees_slot_capacity(api_client) -> None:  # type: ignore[no-untyped-def]
    import pytest as _pytest

    locs = await locations(api_client)
    pt = locs["PT"]  # capacity 4
    menu = await menu_by_slug(api_client, pt["id"])
    slots_before = (
        await api_client.get(f"/locations/{pt['id']}/slots", params={"units": 4})
    ).json()
    empty = [s for s in slots_before["slots"] if s["available"] and s["remaining"] == 4]
    if not empty:
        _pytest.skip("no empty PT slot — reset dev DB")
    target = empty[0]
    item = espresso_item(menu)
    item["quantity"] = 4
    body = order_body(pt["id"], [item], mode="scheduled", pickup_at=target["start"])
    created = await create_order(api_client, body)
    assert created.status_code == 201, created.text
    oid = created.json()["order"]["id"]
    guest = created.json()["access_token"]

    during = (await api_client.get(f"/locations/{pt['id']}/slots", params={"units": 1})).json()
    taken = next(s for s in during["slots"] if s["start"] == target["start"])
    assert taken["remaining"] == 0

    await api_client.post(f"/orders/{oid}/cancel", params={"token": guest})
    after = (await api_client.get(f"/locations/{pt['id']}/slots", params={"units": 1})).json()
    freed = next(s for s in after["slots"] if s["start"] == target["start"])
    assert freed["remaining"] == 4


async def test_double_picked_up_not_allowed(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    created = await create_order(api_client, order_body(tv["id"], [espresso_item(menu)]))
    oid = created.json()["order"]["id"]
    staff = staff_headers(await staff_login(api_client, tv["id"], "1234"))
    for nxt in ("preparing", "ready", "picked_up"):
        await api_client.post(f"/staff/orders/{oid}/status", json={"to_status": nxt}, headers=staff)
    resp = await api_client.post(
        f"/staff/orders/{oid}/status", json={"to_status": "ready"}, headers=staff
    )
    assert resp.status_code == 400
