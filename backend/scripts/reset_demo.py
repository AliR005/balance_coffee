"""Сброс демо: чистит заказы/слоты/счётчики/бонусы, заново сеет меню.

Безопасен для повторного запуска, выполняется за секунды.
PIN баристы и ссылки печатаются в конце (PIN только для демо).
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.db import engine  # noqa: E402
from scripts.seed import main as seed_main  # noqa: E402

CLIENT_URL = "http://localhost:5173"
BARISTA_URL = "http://localhost:5173/staff"


async def main() -> None:
    async with engine.connect() as conn:
        await conn.execute(
            text(
                "TRUNCATE orders, slot_loads, location_day_counters, "
                "bonus_accounts RESTART IDENTITY CASCADE"
            )
        )
        await conn.commit()
    print("demo tables cleared")
    await seed_main()

    import yaml

    data = yaml.safe_load((BACKEND_ROOT / "seed" / "menu.yaml").read_text(encoding="utf-8"))
    print("\n=== balance demo ===")
    for loc in data.get("locations", []):
        print(f"  {loc['name']} ({loc['code']}): PIN баристы {loc.get('staff_pin', '—')}")
    print(f"  клиент:  {CLIENT_URL}")
    print(f"  бариста: {BARISTA_URL}")
    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(CLIENT_URL)
        print("  QR клиентской ссылки:")
        qr.print_ascii(invert=True)
    except ImportError:
        print("  (поставь пакет qrcode, чтобы печатать QR в терминале)")


if __name__ == "__main__":
    asyncio.run(main())
