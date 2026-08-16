import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import Base, SessionLocal, engine, ensure_timescale
from .middleware import RateLimitMiddleware, RequestTrackingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_timescale(db)
        if settings.seed_demo:
            from .seed import seed_demo_data

            seed_demo_data(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    # ── Security middleware (order matters: last added = first executed) ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Device-Key", "X-Request-Id"],
    )
    app.add_middleware(RequestTrackingMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)

    from .api import auth, certificates, devices, ingest, shipments

    prefix = settings.api_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(ingest.router, prefix=prefix)
    app.include_router(shipments.router, prefix=prefix)
    app.include_router(shipments.alerts_router, prefix=prefix)
    app.include_router(devices.router, prefix=prefix)
    app.include_router(certificates.router, prefix=prefix)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()
