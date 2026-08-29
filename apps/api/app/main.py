from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Financial AI Agent Local Fixture API",
        version="0.1.0",
        description="Local-only fixture API. It does not connect to financial services.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    return app


app = create_app()
