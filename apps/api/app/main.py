from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.dashboard import router as dashboard_router
from app.routers.health import router as health_router

# The Vite dev server proxies /api to this app, so the browser normally makes
# same-origin requests and never sends a CORS preflight. These settings stay as
# a second boundary for direct local calls: one loopback origin, read-only
# methods, and an explicit header allowlist.
LOCAL_WEB_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]
ALLOWED_REQUEST_HEADERS = ["Accept", "Accept-Language", "Content-Type"]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Financial AI Agent Local Fixture API",
        version="0.1.0",
        description="Local-only fixture API. It does not connect to financial services.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCAL_WEB_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=ALLOWED_REQUEST_HEADERS,
    )
    app.include_router(health_router)
    app.include_router(dashboard_router)
    return app


app = create_app()
