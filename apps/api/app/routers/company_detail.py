from fastapi import APIRouter

from app.clock import now_kst_iso
from app.fixtures.company_detail import (
    COMPANY_DETAIL_DATA_AS_OF,
    COMPANY_DETAIL_DISCLAIMER,
    COMPANY_DETAIL_SOURCE_LABEL,
    build_company_detail_data,
)
from app.schemas.company_detail import CompanyDetailEnvelope

router = APIRouter(prefix="/api", tags=["company-detail"])


@router.get("/company-detail", response_model=CompanyDetailEnvelope)
def get_company_detail() -> CompanyDetailEnvelope:
    return CompanyDetailEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=COMPANY_DETAIL_DATA_AS_OF,
        sourceLabel=COMPANY_DETAIL_SOURCE_LABEL,
        disclaimer=COMPANY_DETAIL_DISCLAIMER,
        data=build_company_detail_data(),
    )
