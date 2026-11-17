"""FastAPI starter application entrypoint."""

from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from app.base.openapi import OPENAPI_TAG_ORDER, attach_dual_openapi
from app.base.responses import error_response
from app.base.rate_limit import limiter
from app.config.settings import settings
from app.config.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hook (RBAC seed runs after Tortoise init via merged lifespan)."""
    settings.warn_if_weak_local_secrets()
    from app.access.services import seed_default_access_roles

    await seed_default_access_roles()
    yield


# Stock single-schema docs disabled; dual app/admin mounts below when enabled.
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.openapi_enabled else None,
    openapi_tags=OPENAPI_TAG_ORDER,
)
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        retry_after = getattr(exc, "retry_after", None)
        headers = {
            "Retry-After": str(retry_after or 60),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + int(retry_after or 60)),
        }
        limit = getattr(exc, "limit", None)
        if limit is not None:
            headers["X-RateLimit-Limit"] = str(limit)
        return JSONResponse(
            status_code=429,
            content=error_response(
                "Too many requests. Please try again later.",
                code="rate_limited",
            ),
            headers=headers,
        )

    app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def structured_request_logging(request: Request, call_next):
    from app.base.services.observability import structured_log

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    structured_log.log(
        logging.INFO,
        "request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    config=settings.TORTOISE_CONFIG,
    generate_schemas=settings.ENVIRONMENT == "local",
    add_exception_handlers=True,
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

if settings.WHATSAPP_ENABLED:
    from app.whatsapp.client import attach_whatsapp

    attach_whatsapp(app)

if settings.openapi_enabled:
    from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

    attach_dual_openapi(app)

    @app.get("/openapi/app.json", include_in_schema=False)
    async def openapi_app_json():
        return JSONResponse(app.openapi_app())  # type: ignore[attr-defined]

    @app.get("/openapi/admin.json", include_in_schema=False)
    async def openapi_admin_json():
        return JSONResponse(app.openapi_admin())  # type: ignore[attr-defined]

    @app.get("/docs", include_in_schema=False)
    @app.get("/docs/app", include_in_schema=False)
    async def swagger_app():
        return get_swagger_ui_html(
            openapi_url="/openapi/app.json",
            title=f"{settings.PROJECT_NAME} — App",
        )

    @app.get("/docs/admin", include_in_schema=False)
    async def swagger_admin():
        return get_swagger_ui_html(
            openapi_url="/openapi/admin.json",
            title=f"{settings.PROJECT_NAME} — Admin",
        )

    @app.get("/redoc", include_in_schema=False)
    @app.get("/redoc/app", include_in_schema=False)
    async def redoc_app():
        return get_redoc_html(
            openapi_url="/openapi/app.json",
            title=f"{settings.PROJECT_NAME} — App",
        )

    @app.get("/redoc/admin", include_in_schema=False)
    async def redoc_admin():
        return get_redoc_html(
            openapi_url="/openapi/admin.json",
            title=f"{settings.PROJECT_NAME} — Admin",
        )
