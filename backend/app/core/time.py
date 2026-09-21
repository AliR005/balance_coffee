from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def is_open_now(
    opening_hours: dict[str, Any] | None,
    timezone: str,
    now_utc: datetime,
) -> bool:
    """True, если точка открыта в момент now_utc по её часам и поясу."""
    if not opening_hours:
        return False
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        return False
    local = now_utc.astimezone(tz)
    key = WEEKDAYS[local.weekday()]
    intervals = opening_hours.get(key) or []
    now_minutes = local.hour * 60 + local.minute
    for interval in intervals:
        try:
            open_s, close_s = interval
            oh, om = map(int, str(open_s).split(":"))
            ch, cm = map(int, str(close_s).split(":"))
        except (ValueError, TypeError):
            continue
        if oh * 60 + om <= now_minutes < ch * 60 + cm:
            return True
    return False
