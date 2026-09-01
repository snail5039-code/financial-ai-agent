from fastapi import APIRouter

from app.clock import now_kst_iso
from app.fixtures.policy_settings import (
    POLICY_SETTINGS_DATA_AS_OF,
    POLICY_SETTINGS_DISCLAIMER,
    POLICY_SETTINGS_SOURCE_LABEL,
    build_policy_settings_data,
)
from app.schemas.policy_settings import PolicySettingsEnvelope

router = APIRouter(prefix="/api", tags=["policy-settings"])


@router.get("/policy-settings", response_model=PolicySettingsEnvelope)
def get_policy_settings() -> PolicySettingsEnvelope:
    return PolicySettingsEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=POLICY_SETTINGS_DATA_AS_OF,
        sourceLabel=POLICY_SETTINGS_SOURCE_LABEL,
        disclaimer=POLICY_SETTINGS_DISCLAIMER,
        data=build_policy_settings_data(),
    )
