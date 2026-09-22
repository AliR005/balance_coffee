"""Создание заказа: идемпотентность, цена сервера, стоп-лист, слоты, режимы, доступ."""

import uuid

from tests.helpers05 import (
    create_order,
    latte_item,
    locations,
    menu_by_slug,
    milk_cow,
    order_body,
    size_s,
)


async def test_create_on_site_assigns_asap(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    resp = await create_order(api_client, order_body(tv["id"], [latte_item(menu)]))
    assert resp.status_code == 201, resp.text
    order = resp.json()["order"]
    assert order["status"] == "confirmed"
    assert order["mode"] == "on_site"
    assert order["is_asap"] is True
    assert order["code"].startswith("TV-")
    assert resp.json()["access_token"]
    # Снапшот: названия и дельты зафиксированы. Латте M? нет — size S (−3000) + коровье (0).
    item = order["items"][0]
    assert item["product_name"] == "Латте"
    assert order["total"] == 34000 - 3000


async def test_price_recalculated_on_server(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    latte = menu["latte"]
    # L (+6000) + сироп ваниль (+4000), qty 2 → (34000+10000)*2 = 88000.
    syrup = next(
        o["id"]
        for g in latte["groups"]
        if g["key"] == "syrup"
        for o in g["options"]
        if o["name"] == "Ваниль"
    )
    size_l = next(
        o["id"]
        for g in latte["groups"]
        if g["key"] == "size"
        for o in g["options"]
        if o["name"].startswith("L")
    )
    item = {
        "product_id": latte["id"],
        "option_ids": [size_l, milk_cow(latte), syrup],
        "quantity": 2,
    }
    resp = await create_order(api_client, order_body(tv["id"], [item]))
    assert resp.status_code == 201, resp.text
    assert resp.json()["order"]["total"] == 88000


async def test_idempotency_same_body_returns_same_order(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    body = order_body(tv["id"], [latte_item(menu)])
    key = f"idem-same-{uuid.uuid4().hex[:8]}"
    first = await create_order(api_client, body, key=key)
    second = await create_order(api_client, body, key=key)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["order"]["id"] == second.json()["order"]["id"]
    assert first.json()["access_token"] == second.json()["access_token"]


async def test_idempotency_different_body_conflicts(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    body = order_body(tv["id"], [latte_item(menu)])
    key = f"idem-diff-{uuid.uuid4().hex[:8]}"
    await create_order(api_client, body, key=key)
    body["comment"] = "другой текст"
    resp = await create_order(api_client, body, key=key)
    assert resp.status_code == 400
    assert resp.json()["code"] == "idempotency_conflict"


async def test_idempotency_key_required(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    resp = await api_client.post("/orders", json=order_body(tv["id"], []))
    assert resp.status_code in (400, 422)


async def test_unavailable_product_rejected(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    cold = menu["cold-brew"]  # в стоп-листе TV
    item = {"product_id": cold["id"], "option_ids": [size_s(cold)], "quantity": 1}
    resp = await create_order(api_client, order_body(tv["id"], [item]))
    assert resp.status_code == 400
    assert resp.json()["code"] == "product_unavailable"


async def test_unavailable_option_rejected(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    latte = menu["latte"]
    coconut = next(
        o["id"]
        for g in latte["groups"]
        if g["key"] == "milk"
        for o in g["options"]
        if o["name"] == "Кокосовое"
    )
    item = {"product_id": latte["id"], "option_ids": [size_s(latte), coconut], "quantity": 1}
    resp = await create_order(api_client, order_body(tv["id"], [item]))
    assert resp.status_code == 400
    assert resp.json()["code"] == "option_unavailable"


async def test_order_too_large(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    pt = locs["PT"]  # capacity 4
    menu = await menu_by_slug(api_client, pt["id"])
    esp = menu["espresso"]
    item = {"product_id": esp["id"], "option_ids": [size_s(esp)], "quantity": 5}
    resp = await create_order(api_client, order_body(pt["id"], [item]))
    assert resp.status_code == 400
    assert resp.json()["code"] == "order_too_large"


async def test_scheduled_outside_hours(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    body = order_body(
        tv["id"], [latte_item(menu)], mode="scheduled", pickup_at="2026-09-22T00:00:00Z"
    )
    resp = await create_order(api_client, body)
    assert resp.status_code == 400
    assert resp.json()["code"] in ("outside_hours", "slot_unavailable")


async def test_scheduled_needs_pickup_at(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    body = order_body(tv["id"], [latte_item(menu)], mode="scheduled")
    resp = await create_order(api_client, body)
    assert resp.status_code == 400


async def test_guest_access(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    menu = await menu_by_slug(api_client, tv["id"])
    created = await create_order(api_client, order_body(tv["id"], [latte_item(menu)]))
    oid = created.json()["order"]["id"]
    token = created.json()["access_token"]

    assert (await api_client.get(f"/orders/{oid}")).status_code == 401
    bad = await api_client.get(f"/orders/{oid}", params={"token": "wrong"})
    assert bad.status_code == 401
    ok = await api_client.get(f"/orders/{oid}", params={"token": token})
    assert ok.status_code == 200
    assert ok.json()["id"] == oid

    assert (await api_client.get("/orders/999999", params={"token": token})).status_code == 404


async def test_malformed_body_returns_json_422(api_client) -> None:  # type: ignore[no-untyped-def]
    # Тело без Content-Type: ответ — JSON 422, соединение не рвётся.
    resp = await api_client.post(
        "/orders", content=b'{"location_id": 1', headers={"Idempotency-Key": "malformed-1"}
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"
