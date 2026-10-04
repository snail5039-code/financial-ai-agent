from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import config
from app.db import connect
from app.routers import auth, policy


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="invest-agent-api")
    app.state.database_url = database_url or config.DATABASE_URL
    app.include_router(auth.router)
    app.include_router(policy.router)

    @app.exception_handler(RequestValidationError)
    def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        # 오류 형식을 {"detail": "사람이 읽을 수 있는 이유"}로 맞춘다 (06-api-spec.md)
        first = error.errors()[0]
        field = ".".join(str(part) for part in first["loc"][1:])
        reason = first["msg"].removeprefix("Value error, ")
        return JSONResponse({"detail": f"{field}: {reason}" if field else reason}, status_code=422)

    @app.get("/api/health")
    def health() -> JSONResponse:
        try:
            with connect(app.state.database_url) as conn:
                conn.execute("SELECT 1")
        except Exception:
            return JSONResponse({"status": "degraded", "db": "error"}, status_code=503)
        return JSONResponse({"status": "ok", "db": "ok"})

    return app


app = create_app()
