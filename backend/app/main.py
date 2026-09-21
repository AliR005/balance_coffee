import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, get_logger
from app.health import router as health_router

log = get_logger("app")


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(title="Balance API")

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        log.info(
            "request",
            path=request.url.path,
            method=request.method,
            request_id=request_id,
            elapsed_ms=elapsed_ms,
        )
        return response

    register_error_handlers(app)
    app.include_router(health_router)
    from app.modules.menu.router import router as menu_router

    app.include_router(menu_router)

    @app.get("/db-check")
    async def _db_check() -> dict[str, str]:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
