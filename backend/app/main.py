"""Cordis — AI-powered crisis coordination platform.

From distress call to resource dispatch. Combines emergency triage (Whisper, ONNX)
with logistics coordination (Gemini multi-agent pipeline).
"""

from __future__ import annotations

import logging
import sys
import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse
from starlette_prometheus import PrometheusMiddleware, metrics

from app.core.config import settings
from app.core.redis_client import close_redis, init_redis
from app.core.database import engine
from app.api.v1.api import api_router
from app.core.security import limiter, require_jwt_token
from app.models.base import Base

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

# ---------------------------------------------------------------------------
# structlog JSON configuration
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger("cordis.app")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


def _register_logistics_tools() -> None:
    """Import logistics tool modules to trigger tool_registry.register() calls."""
    try:
        import app.services.logistics.tools.task_tools  # noqa: F401
        import app.services.logistics.tools.calendar_tool  # noqa: F401
        import app.services.logistics.tools.knowledge_tool  # noqa: F401
        import app.services.logistics.tools.weather_tool  # noqa: F401
        import app.services.logistics.tools.route_tool  # noqa: F401
        import app.services.logistics.tools.disaster_feed  # noqa: F401
        log.info("logistics tools registered")
    except Exception as e:
        log.warning("logistics tools registration failed", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------- Startup -----------
    if not settings.SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set via environment variable")

    if settings.APP_ENV.lower() == "production" and not settings.POSTGRES_PASSWORD:
        raise RuntimeError("POSTGRES_PASSWORD must be set in production")

    if settings.APP_ENV.lower() == "production" and settings.ENABLE_DOCS:
        log.warning("ENABLE_DOCS=true in production; docs endpoint is being force-disabled")

    if any(origin == "*" for origin in settings.ALLOWED_ORIGINS):
        raise RuntimeError("Wildcard CORS origin is not allowed")

    # Redis
    await init_redis()

    # Database schema (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))

    # Create logistics tables (separate Base)
    if settings.LOGISTICS_ENABLED:
        try:
            from app.models.logistics import Base as LogisticsBase
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: LogisticsBase.metadata.create_all(sync_conn, checkfirst=True))
            log.info("logistics tables created")
        except Exception as e:
            log.warning("logistics table creation failed (pgvector may be required)", error=str(e))

    # Whisper STT model (CPU), loaded off event loop
    from app.services.whisper_service import WhisperService
    whisper_service = WhisperService(model_size=settings.WHISPER_MODEL_SIZE)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, whisper_service.initialize)
    app.state.whisper_service = whisper_service

    # Intent ONNX model
    from app.ml.intent_model_loader import IntentModelLoader
    intent_loader = IntentModelLoader()
    await intent_loader.initialize()
    app.state.intent_loader = intent_loader

    # Register logistics tools
    if settings.LOGISTICS_ENABLED:
        _register_logistics_tools()

    # Background event subscriber
    from app.core.event_listener import start_event_listener
    start_event_listener()

    log.info("cordis started", logistics=settings.LOGISTICS_ENABLED)
    yield

    # ----------- Shutdown -----------
    from app.core.event_listener import stop_event_listener
    await stop_event_listener()
    await close_redis()
    if getattr(app.state, "emotion_loader", None) is not None:
        await app.state.emotion_loader.shutdown()
    if getattr(app.state, "intent_loader", None) is not None:
        await app.state.intent_loader.shutdown()
    if getattr(app.state, "whisper_service", None) is not None:
        app.state.whisper_service.shutdown()
    log.info("cordis shut down cleanly")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

docs_enabled = settings.ENABLE_DOCS and settings.APP_ENV.lower() != "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Open-source AI crisis coordination — from distress call to resource dispatch.",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs_enabled else None,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(PrometheusMiddleware)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.websockets.connection_manager import router as websocket_router  # noqa: E402
from app.dashboard.routes import router as dashboard_router  # noqa: E402
from app.api.v1.endpoints.emergency import router as emergency_router  # noqa: E402

app.include_router(api_router, prefix=settings.API_V1_STR, dependencies=[Depends(require_jwt_token)])
app.include_router(emergency_router, dependencies=[Depends(require_jwt_token)])
app.include_router(websocket_router, prefix="/ws", tags=["websockets"])
app.include_router(dashboard_router, tags=["dashboard"], dependencies=[Depends(require_jwt_token)])


@app.get("/metrics", include_in_schema=False, dependencies=[Depends(require_jwt_token)])
async def protected_metrics(request: Request) -> StarletteResponse:
    return await metrics(request)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    from app.core.database import check_db_health
    db_ok = await check_db_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "project": "cordis",
        "logistics_enabled": settings.LOGISTICS_ENABLED,
    }
