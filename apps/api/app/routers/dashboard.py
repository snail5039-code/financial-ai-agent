from fastapi import APIRouter

from app.clock import now_kst_iso
from app.fixtures.dashboard import (
    DASHBOARD_DATA_AS_OF,
    DASHBOARD_DISCLAIMER,
    DASHBOARD_SOURCE_LABEL,
    build_dashboard_data,
)
from app.schemas.dashboard import DashboardEnvelope

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardEnvelope)
def get_dashboard() -> DashboardEnvelope:
    """Return the local dashboard fixture.

    Read only. No account, order, quote, disclosure, or external API is touched.
    """
    return DashboardEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=DASHBOARD_DATA_AS_OF,
        sourceLabel=DASHBOARD_SOURCE_LABEL,
        disclaimer=DASHBOARD_DISCLAIMER,
        data=build_dashboard_data(),
    )
