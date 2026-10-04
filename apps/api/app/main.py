from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import config
from app.db import connect


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="invest-agent-api")

    @app.get("/api/health")
    def health() -> JSONResponse:
        try:
            with connect(database_url or config.DATABASE_URL) as conn:
                conn.execute("SELECT 1")
        except Exception:
            return JSONResponse({"status": "degraded", "db": "error"}, status_code=503)
        return JSONResponse({"status": "ok", "db": "ok"})

    return app


app = create_app()
