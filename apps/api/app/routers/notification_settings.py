from fastapi import APIRouter

from app.clock import now_kst_iso
from app.fixtures.notification_settings import (
    NOTIFICATION_SETTINGS_DATA_AS_OF,
    NOTIFICATION_SETTINGS_DISCLAIMER,
    NOTIFICATION_SETTINGS_SOURCE_LABEL,
    build_notification_settings_data,
)
from app.schemas.notification_settings import NotificationSettingsEnvelope

router = APIRouter(prefix="/api", tags=["notification-settings"])


@router.get("/notification-settings", response_model=NotificationSettingsEnvelope)
def get_notification_settings() -> NotificationSettingsEnvelope:
    return NotificationSettingsEnvelope(
        generatedAt=now_kst_iso(),
        dataAsOf=NOTIFICATION_SETTINGS_DATA_AS_OF,
        sourceLabel=NOTIFICATION_SETTINGS_SOURCE_LABEL,
        disclaimer=NOTIFICATION_SETTINGS_DISCLAIMER,
        data=build_notification_settings_data(),
    )
