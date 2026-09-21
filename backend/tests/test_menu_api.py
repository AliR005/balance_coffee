"""API меню/точек/котировки поверх seed-данных (read-only, идемпотентны)."""


async def _locations(api_client):  # type: ignore[no-untyped-def]
    resp = await api_client.get("/locations")
    assert resp.status_code == 200
    return resp.json()


async def test_locations_have_open_flag(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await _locations(api_client)
    assert len(locs) >= 2
    codes = {loc["code"] for loc in locs}
    assert {"TV", "PT"} <= codes
    for loc in locs:
        assert isinstance(loc["is_open_now"], bool)


async def test_menu_stoplist_differs_per_location(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}

    tv = (await api_client.get(f"/locations/{locs['TV']['id']}/menu")).json()
    pt = (await api_client.get(f"/locations/{locs['PT']['id']}/menu")).json()

    def prod_map(menu):  # type: ignore[no-untyped-def]
        out = {}
        for cat in menu["categories"]:
            for prod in cat["products"]:
                opts = {o["name"]: o for g in prod["groups"] for o in g["options"]}
                out[prod["slug"]] = (prod["available"], opts)
        return out

    tv_map, pt_map = prod_map(tv), prod_map(pt)
    # Колд брю недоступен на TV, но доступен на PT
    assert tv_map["cold-brew"][0] is False
    assert pt_map["cold-brew"][0] is True
    # Кокосовое молоко недоступно на TV
    assert tv_map["latte"][1]["Кокосовое"]["available"] is False
    assert pt_map["latte"][1]["Кокосовое"]["available"] is True


async def test_menu_has_video_fields(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = await _locations(api_client)
    menu = (await api_client.get(f"/locations/{locs[0]['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    assert by_slug["espresso"]["video_duration_sec"] == 9
    assert by_slug["espresso"]["video_steps"][0]["title"] == "Эспрессо"


async def test_quote_ok(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}
    menu = (await api_client.get(f"/locations/{locs['PT']['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    latte = by_slug["latte"]

    def opt(name):  # type: ignore[no-untyped-def]
        for g in latte["groups"]:
            for o in g["options"]:
                if o["name"] == name:
                    return o["id"]
        raise AssertionError(name)

    # латте M (0) + овсяное (+5000), qty 2: (34000+5000)*2 = 78000
    payload = {
        "items": [
            {
                "product_id": latte["id"],
                "option_ids": [opt("M · 300 мл"), opt("Овсяное")],
                "quantity": 2,
            }
        ]
    }
    resp = await api_client.post(f"/locations/{locs['PT']['id']}/quote", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 78000


async def test_quote_negative_delta(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}
    menu = (await api_client.get(f"/locations/{locs['PT']['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    esp = by_slug["espresso"]

    def opt(name):  # type: ignore[no-untyped-def]
        for g in esp["groups"]:
            for o in g["options"]:
                if o["name"] == name:
                    return o["id"]
        raise AssertionError(name)

    payload = {
        "items": [{"product_id": esp["id"], "option_ids": [opt("S · 200 мл")], "quantity": 1}]
    }
    resp = await api_client.post(f"/locations/{locs['PT']['id']}/quote", json=payload)
    assert resp.status_code == 200
    assert resp.json()["total"] == 22000 - 3000


async def test_quote_unavailable_product(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}
    menu = (await api_client.get(f"/locations/{locs['TV']['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    cold = by_slug["cold-brew"]
    size_id = cold["groups"][0]["options"][0]["id"]
    resp = await api_client.post(
        f"/locations/{locs['TV']['id']}/quote",
        json={"items": [{"product_id": cold["id"], "option_ids": [size_id], "quantity": 1}]},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "product_unavailable"


async def test_quote_unavailable_option(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}
    menu = (await api_client.get(f"/locations/{locs['TV']['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    latte = by_slug["latte"]

    def opt(name):  # type: ignore[no-untyped-def]
        for g in latte["groups"]:
            for o in g["options"]:
                if o["name"] == name:
                    return o["id"]
        raise AssertionError(name)

    payload = {
        "items": [
            {
                "product_id": latte["id"],
                "option_ids": [opt("M · 300 мл"), opt("Кокосовое")],
                "quantity": 1,
            }
        ]
    }
    resp = await api_client.post(f"/locations/{locs['TV']['id']}/quote", json=payload)
    assert resp.status_code == 400
    assert resp.json()["code"] == "option_unavailable"


async def test_quote_missing_required_group(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}
    menu = (await api_client.get(f"/locations/{locs['PT']['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    latte = by_slug["latte"]
    resp = await api_client.post(
        f"/locations/{locs['PT']['id']}/quote",
        json={"items": [{"product_id": latte["id"], "option_ids": [], "quantity": 1}]},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"


async def test_quote_too_many_units(api_client) -> None:  # type: ignore[no-untyped-def]
    locs = {loc["code"]: loc for loc in await _locations(api_client)}
    menu = (await api_client.get(f"/locations/{locs['PT']['id']}/menu")).json()
    by_slug = {p["slug"]: p for c in menu["categories"] for p in c["products"]}
    esp = by_slug["espresso"]
    size_id = esp["groups"][0]["options"][0]["id"]
    items = [{"product_id": esp["id"], "option_ids": [size_id], "quantity": 10} for _ in range(3)]
    resp = await api_client.post(f"/locations/{locs['PT']['id']}/quote", json={"items": items})
    assert resp.status_code == 400


async def test_menu_unknown_location(api_client) -> None:  # type: ignore[no-untyped-def]
    resp = await api_client.get("/locations/999999/menu")
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"
