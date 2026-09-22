"""Слоты: чистая логика сетки + структурные свойства API."""

from datetime import UTC, datetime

from app.core.time import WEEKDAYS
from app.modules.menu.models import Location
from app.modules.orders.service import ceil_to_step, day_slots_utc


def _loc(**kw):  # type: ignore[no-untyped-def]
    base = dict(
        code="T",
        name="T",
        timezone="Europe/Moscow",
        opening_hours={d: [["08:00", "22:00"]] for d in WEEKDAYS},
        lead_time_min=10,
        slot_step_min=15,
        slot_capacity=6,
    )
    base.update(kw)
    return Location(**base)


def utc(y: int, mo: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def test_ceil_to_step() -> None:
    # 10:07 MSK при шаге 15 → 10:15.
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("Europe/Moscow")
    assert ceil_to_step(datetime(2026, 9, 21, 10, 7, tzinfo=tz), 15) == datetime(
        2026, 9, 21, 10, 15, tzinfo=tz
    )
    assert ceil_to_step(datetime(2026, 9, 21, 10, 0, tzinfo=tz), 15) == datetime(
        2026, 9, 21, 10, 0, tzinfo=tz
    )


def test_first_slot_respects_lead_time() -> None:
    # Пн 10:07 MSK → now+10 = 10:17 → округление 10:30 MSK = 07:30 UTC.
    slots, is_open = day_slots_utc(_loc(), utc(2026, 9, 21, 7, 7))
    assert is_open is True
    assert slots[0] == utc(2026, 9, 21, 7, 30)


def test_closed_day() -> None:
    loc = _loc(opening_hours={d: ([["08:00", "22:00"]] if d != "sun" else []) for d in WEEKDAYS})
    slots, is_open = day_slots_utc(loc, utc(2026, 9, 27, 9))  # воскресенье
    assert slots == [] and is_open is False


def test_slots_aligned_and_bounded() -> None:
    slots, _ = day_slots_utc(_loc(), utc(2026, 9, 21, 5))  # 08:00 MSK
    assert slots == sorted(slots)
    # Последний старт не позже закрытия (22:00 MSK = 19:00 UTC), шаг 15.
    assert slots[-1] == utc(2026, 9, 21, 19, 0)
    assert all(s.minute % 15 == 0 and s.second == 0 for s in slots)


async def test_slots_api_structure(api_client) -> None:  # type: ignore[no-untyped-def]
    from tests.helpers05 import locations

    locs = await locations(api_client)
    tv = locs["TV"]
    data = (await api_client.get(f"/locations/{tv['id']}/slots", params={"units": 2})).json()
    assert data["open"] is True
    assert data["units"] == 2
    assert data["asap"] is not None
    assert data["asap"]["start"] == next(s["start"] for s in data["slots"] if s["available"])
    # Флаги согласованы с остатком (БД общая с другими тестами — точные числа не фиксируем).
    assert all(s["available"] == (s["remaining"] >= 2) for s in data["slots"])
    assert all(0 <= s["remaining"] <= 6 for s in data["slots"])


async def test_slots_units_bigger_than_capacity(api_client) -> None:  # type: ignore[no-untyped-def]
    from tests.helpers05 import locations

    locs = await locations(api_client)
    pt = locs["PT"]
    resp = await api_client.get(f"/locations/{pt['id']}/slots", params={"units": 99})
    assert resp.status_code == 400
    assert resp.json()["code"] == "order_too_large"


async def test_slots_unknown_location(api_client) -> None:  # type: ignore[no-untyped-def]
    resp = await api_client.get("/locations/999999/slots")
    assert resp.status_code == 404
