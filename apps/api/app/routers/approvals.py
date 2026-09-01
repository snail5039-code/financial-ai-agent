from typing import Literal

from fastapi import APIRouter, HTTPException, Request

from app.clock import now_kst_iso
from app.fixtures.approvals import (
    APPROVALS_DATA_AS_OF,
    APPROVALS_DISCLAIMER,
    APPROVALS_SOURCE_LABEL,
)
from app.schemas.approvals import ApprovalActionEnvelope, ApprovalsData, ApprovalsEnvelope
from app.store.approvals import ApprovalStore, DecisionConflictError

router = APIRouter(prefix="/api", tags=["approvals"])


def _store(request: Request) -> ApprovalStore:
    return request.app.state.approval_store


@router.get("/approvals", response_model=ApprovalsEnvelope)
def list_approvals(request: Request) -> ApprovalsEnvelope:
    return ApprovalsEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=APPROVALS_DATA_AS_OF,
        sourceLabel=APPROVALS_SOURCE_LABEL,
        disclaimer=APPROVALS_DISCLAIMER,
        data=ApprovalsData(orders=_store(request).list()),
    )


def _decide(request: Request, decision_id: str, status: Literal["approved", "rejected"]) -> ApprovalActionEnvelope:
    store = _store(request)
    if store.get(decision_id) is None:
        raise HTTPException(status_code=404, detail=f"unknown decision id: {decision_id}")

    try:
        updated = store.decide(decision_id, status)
    except DecisionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"{decision_id}은(는) 이미 {exc.order.decisionStatus} 상태라 다시 결정할 수 없습니다.",
        ) from exc

    return ApprovalActionEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=APPROVALS_DATA_AS_OF,
        sourceLabel=APPROVALS_SOURCE_LABEL,
        disclaimer=APPROVALS_DISCLAIMER,
        data=updated,
    )


@router.post("/approvals/{decision_id}/approve", response_model=ApprovalActionEnvelope)
def approve_order(decision_id: str, request: Request) -> ApprovalActionEnvelope:
    """Mark a local demo order approved. No real order is created or sent anywhere."""
    return _decide(request, decision_id, "approved")


@router.post("/approvals/{decision_id}/reject", response_model=ApprovalActionEnvelope)
def reject_order(decision_id: str, request: Request) -> ApprovalActionEnvelope:
    """Mark a local demo order rejected. This only changes in-memory demo state."""
    return _decide(request, decision_id, "rejected")
