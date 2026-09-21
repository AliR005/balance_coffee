from datetime import UTC, datetime

from app.core.time import is_open_now

HOURS = {
    "mon": [["08:00", "22:00"]],
    "tue": [["08:00", "22:00"]],
    "wed": [["08:00", "22:00"]],
    "thu": [["08:00", "22:00"]],
    "fri": [["08:00", "23:00"]],
    "sat": [["09:00", "23:00"]],
    "sun": [],
}


def utc(y: int, mo: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def test_open_inside_hours() -> None:
    # Пн 10:00 MSK = 07:00 UTC
    assert is_open_now(HOURS, "Europe/Moscow", utc(2026, 9, 21, 7)) is True


def test_open_boundary_open_inclusive() -> None:
    # Открытие 08:00 MSK = 05:00 UTC — открыто
    assert is_open_now(HOURS, "Europe/Moscow", utc(2026, 9, 21, 5)) is True


def test_open_boundary_close_exclusive() -> None:
    # Закрытие 22:00 MSK = 19:00 UTC — уже закрыто
    assert is_open_now(HOURS, "Europe/Moscow", utc(2026, 9, 21, 19)) is False


def test_closed_day() -> None:
    # Вс — закрыто весь день
    assert is_open_now(HOURS, "Europe/Moscow", utc(2026, 9, 27, 9)) is False


def test_timezone_matters() -> None:
    # 07:00 UTC: в Москве 10:00 (открыто), в Новосибирске 14:00 (смотрим те же часы — открыто),
    # а в Калининграде 09:00... берём точку с America/New_York: там 03:00 ночи — закрыто.
    assert is_open_now(HOURS, "America/New_York", utc(2026, 9, 21, 7)) is False


def test_empty_hours_closed() -> None:
    assert is_open_now({}, "Europe/Moscow", utc(2026, 9, 21, 7)) is False
    assert is_open_now(None, "Europe/Moscow", utc(2026, 9, 21, 7)) is False
