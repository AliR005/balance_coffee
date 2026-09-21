"""Export OpenAPI schema to web/openapi.json."""

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app  # noqa: E402


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/openapi.json")
    app = create_app()
    schema = app.openapi()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
