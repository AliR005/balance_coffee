"""Staff: вход, изоляция точек, стоп-лист и его влияние."""

import pytest

from app.modules.staff import service as staff_service
from tests.helpers05 import (
    create_order,
    latte_item,
    locations,
    menu_by_slug,
    order_body,
    staff_headers,
    staff_login,
)


@pytest.fixture(autouse=True)
def _fresh_rate_limit():  # type: ignore[no-untyped-def]
    # Лимит in-memory на процесс — изолируем тесты друг от друга.
    staff_service._LOGIN_ATTEMPTS.clear()
    yield
    staff_service._LOGIN_ATTEMPTS.clear()


async def test_login_ok_and_wrong_pin(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    token = await staff_login(api_client, tv["id"], "1234")
    assert token
    bad = await api_client.post("/staff/login", json={"location_id": tv["id"], "pin": "0000"})
    assert bad.status_code == 401
    unknown = await api_client.post("/staff/login", json={"location_id": 999999, "pin": "1234"})
    assert unknown.status_code == 401


async def test_login_rate_limit(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    for _ in range(10):
        await api_client.post("/staff/login", json={"location_id": tv["id"], "pin": "0000"})
    # 11-я попытка (даже с верным PIN) тоже 401 — лимит не выдаёт себя.
    limited = await api_client.post("/staff/login", json={"location_id": tv["id"], "pin": "1234"})
    assert limited.status_code == 401


async def test_staff_endpoints_need_token(api_client) -> None:  # type: ignore[no-untyped-def]
    assert (await api_client.get("/staff/orders")).status_code == 401
    assert (await api_client.get("/staff/availability")).status_code == 401


async def test_orders_scoped_to_location(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv, pt = locs["TV"], locs["PT"]
    menu_tv = await menu_by_slug(api_client, tv["id"])
    created = await create_order(api_client, order_body(tv["id"], [latte_item(menu_tv)]))
    oid = created.json()["order"]["id"]

    pt_token = staff_headers(await staff_login(api_client, pt["id"], "4321"))
    tv_token = staff_headers(await staff_login(api_client, tv["id"], "1234"))

    pt_orders = (await api_client.get("/staff/orders", headers=pt_token)).json()
    assert all(o["location_id"] == pt["id"] for o in pt_orders)
    assert oid not in [o["id"] for o in pt_orders]
    tv_orders = (await api_client.get("/staff/orders", headers=tv_token)).json()
    assert oid in [o["id"] for o in tv_orders]

    # Чужая точка: смена статуса — 404, как будто заказа нет.
    resp = await api_client.post(
        f"/staff/orders/{oid}/status", json={"to_status": "preparing"}, headers=pt_token
    )
    assert resp.status_code == 404


async def test_stoplist_affects_menu_and_orders(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    pt = locs["PT"]
    token = staff_headers(await staff_login(api_client, pt["id"], "4321"))
    menu = await menu_by_slug(api_client, pt["id"])
    raf = menu["raf"]

    # Выключаем раф на PT.
    resp = await api_client.put(
        f"/staff/availability/products/{raf['id']}", json={"is_available": False}, headers=token
    )
    assert resp.status_code == 200

    menu2 = await menu_by_slug(api_client, pt["id"])
    assert menu2["raf"]["available"] is False

    from tests.helpers05 import size_s

    milk_group = next(g for g in raf["groups"] if g["key"] == "milk")
    milk = next(o["id"] for o in milk_group["options"] if o["available"])
    item = {"product_id": raf["id"], "option_ids": [size_s(raf), milk], "quantity": 1}
    denied = await create_order(api_client, order_body(pt["id"], [item]))
    assert denied.status_code == 400
    assert denied.json()["code"] == "product_unavailable"

    # Включаем обратно.
    resp = await api_client.put(
        f"/staff/availability/products/{raf['id']}", json={"is_available": True}, headers=token
    )
    assert resp.status_code == 200
    menu3 = await menu_by_slug(api_client, pt["id"])
    assert menu3["raf"]["available"] is True


async def test_option_stoplist(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    token = staff_headers(await staff_login(api_client, tv["id"], "1234"))
    avail = (await api_client.get("/staff/availability", headers=token)).json()
    oat = next(o for o in avail["options"] if o["name"] == "Овсяное")
    assert oat["available"] is True

    await api_client.put(
        f"/staff/availability/options/{oat['id']}", json={"is_available": False}, headers=token
    )
    avail2 = (await api_client.get("/staff/availability", headers=token)).json()
    assert next(o for o in avail2["options"] if o["name"] == "Овсяное")["available"] is False

    menu = await menu_by_slug(api_client, tv["id"])
    milk_opts = next(g for g in menu["latte"]["groups"] if g["key"] == "milk")["options"]
    cow = next(o["id"] for o in milk_opts if o["name"] == "Коровье")
    item = latte_item(menu)
    item["option_ids"] = [oat["id"] if oid == cow else oid for oid in item["option_ids"]]
    denied = await create_order(api_client, order_body(tv["id"], [item]))
    assert denied.json()["code"] == "option_unavailable"

    await api_client.put(
        f"/staff/availability/options/{oat['id']}", json={"is_available": True}, headers=token
    )


async def test_availability_unknown_ids(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await locations(api_client)
    tv = locs["TV"]
    token = staff_headers(await staff_login(api_client, tv["id"], "1234"))
    assert (
        await api_client.put(
            "/staff/availability/products/999999", json={"is_available": False}, headers=token
        )
    ).status_code == 404
    assert (
        await api_client.put(
            "/staff/availability/options/999999", json={"is_available": False}, headers=token
        )
    ).status_code == 404
