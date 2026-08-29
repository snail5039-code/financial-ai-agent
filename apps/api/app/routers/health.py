from datetime import datetime, timezone, timedelta

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])

KST = timezone(timedelta(hours=9), name="KST")


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    now = datetime.now(KST).isoformat()
    return HealthResponse(
        status="ok",
        service="financial-ai-agent-api",
        generatedAt=now,
        dataAsOf=now,
        sourceLabel="local FastAPI health",
        isMock=True,
        paperOnly=True,
        externalConnections=0,
        executed=False,
        disclaimer=(
            "Local development status only. "
            "No real financial data, execution, market data, external API, "
            "or persistent storage is connected."
        ),
    )
