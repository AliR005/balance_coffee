"""Общие хелперы тестов фазы 05 (поверх seed-данных)."""

import uuid


async def locations(client):  # type: ignore[no-untyped-def]
    resp = await client.get("/locations")
    assert resp.status_code == 200
    return {loc["code"]: loc for loc in resp.json()}


async def menu_by_slug(client, location_id: int):  # type: ignore[no-untyped-def]
    resp = await client.get(f"/locations/{location_id}/menu")
    assert resp.status_code == 200
    return {p["slug"]: p for c in resp.json()["categories"] for p in c["products"]}


def size_s(product: dict) -> int:  # type: ignore[type-arg]
    for group in product["groups"]:
        if group["key"] == "size":
            for opt in group["options"]:
                if opt["name"].startswith("S"):
                    return opt["id"]
    raise AssertionError("no size S")


def milk_cow(product: dict) -> int:  # type: ignore[type-arg]
    for group in product["groups"]:
        if group["key"] == "milk":
            for opt in group["options"]:
                if opt["name"] == "Коровье":
                    return opt["id"]
    raise AssertionError("no cow milk")


def order_body(location_id: int, items: list, **kw):  # type: ignore[type-arg]
    body = {
        "location_id": location_id,
        "mode": "on_site",
        "items": items,
        "customer_name": "Тест",
        "customer_phone": "+70000000001",
    }
    body.update(kw)
    return body


async def create_order(client, body: dict, key: str | None = None):  # type: ignore[type-arg]
    return await client.post(
        "/orders", json=body, headers={"Idempotency-Key": key or f"key-{uuid.uuid4()}"}
    )


async def staff_login(client, location_id: int, pin: str):  # type: ignore[no-untyped-def]
    resp = await client.post("/staff/login", json={"location_id": location_id, "pin": pin})
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def staff_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def latte_item(menu: dict, qty: int = 1) -> dict:  # type: ignore[type-arg]
    latte = menu["latte"]
    return {
        "product_id": latte["id"],
        "option_ids": [size_s(latte), milk_cow(latte)],
        "quantity": qty,
    }


def espresso_item(menu: dict, qty: int = 1) -> dict:  # type: ignore[type-arg]
    esp = menu["espresso"]
    return {"product_id": esp["id"], "option_ids": [size_s(esp)], "quantity": qty}
