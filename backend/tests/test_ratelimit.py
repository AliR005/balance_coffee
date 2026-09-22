"""Rate limit POST /orders: 429 + rate_limited при превышении."""

import app.core.ratelimit as ratelimit
from tests.helpers05 import create_order, latte_item, locations, menu_by_slug, order_body


async def test_orders_rate_limited(api_client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setitem(ratelimit.LIMITS, "/orders", (2, 60))
    ratelimit._hits.clear()
    try:
        locs = await locations(api_client)
        tv = locs["TV"]
        menu = await menu_by_slug(api_client, tv["id"])
        body = order_body(tv["id"], [latte_item(menu)])
        assert (await create_order(api_client, body)).status_code == 201
        assert (await create_order(api_client, body)).status_code == 201
        third = await create_order(api_client, body)
        assert third.status_code == 429
        assert third.json()["code"] == "rate_limited"
    finally:
        ratelimit._hits.clear()
