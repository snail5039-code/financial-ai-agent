from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.account import router as account_router
from app.routers.agents import router as agents_router
from app.routers.approvals import router as approvals_router
from app.routers.dashboard import router as dashboard_router
from app.routers.health import router as health_router
from app.store.approvals import ApprovalStore

# The Vite dev server proxies /api to this app, so the browser normally makes
# same-origin requests and never sends a CORS preflight. These settings stay as
# a second boundary for direct local calls: one loopback origin, an explicit
# method allowlist (GET plus POST for the approve/reject demo actions), and an
# explicit header allowlist.
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
        allow_methods=["GET", "POST"],
        allow_headers=ALLOWED_REQUEST_HEADERS,
    )
    # One store per app instance (not a module-level singleton) so tests that
    # each call create_app() get independent, isolated demo state.
    app.state.approval_store = ApprovalStore()

    app.include_router(health_router)
    app.include_router(dashboard_router)
    app.include_router(account_router)
    app.include_router(agents_router)
    app.include_router(approvals_router)
    return app


app = create_app()
