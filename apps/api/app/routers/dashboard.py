from fastapi import APIRouter, Request

from app.clock import now_kst_iso
from app.fixtures.dashboard import (
    DASHBOARD_DATA_AS_OF,
    DASHBOARD_DISCLAIMER,
    DASHBOARD_SOURCE_LABEL,
    build_dashboard_data,
)
from app.fixtures.decisions import DEC_1042
from app.schemas.dashboard import DashboardEnvelope

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardEnvelope)
def get_dashboard(request: Request) -> DashboardEnvelope:
    """Return the local dashboard fixture.

    Read only. No account, order, quote, disclosure, or external API is touched.

    The featured decision (DEC-1042) reads its live pending/approved/rejected
    state from the same approval store the approvals queue writes to, so
    approving it from either screen is reflected on both immediately.
    """
    order = request.app.state.approval_store.get(DEC_1042.id)
    decision_status = order.decisionStatus if order is not None else "pending"
    decided_at = order.decidedAt if order is not None else None

    return DashboardEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=DASHBOARD_DATA_AS_OF,
        sourceLabel=DASHBOARD_SOURCE_LABEL,
        disclaimer=DASHBOARD_DISCLAIMER,
        data=build_dashboard_data(decision_status=decision_status, decided_at=decided_at),
    )
