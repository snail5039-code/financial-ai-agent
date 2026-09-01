from fastapi.testclient import TestClient

from app.main import create_app


def get_payload() -> dict:
    client = TestClient(create_app())
    response = client.get("/api/notification-settings")
    assert response.status_code == 200
    return response.json()


def test_envelope_carries_safety_flags() -> None:
    payload = get_payload()
    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0


def test_returns_four_channels_and_six_types() -> None:
    data = get_payload()["data"]
    assert len(data["channels"]) == 4
    assert len(data["types"]) == 6
    assert data["defaultSeverity"] in ("중대", "높음", "보통")


def test_only_in_app_channel_is_enabled_by_default() -> None:
    channels = {c["id"]: c["enabled"] for c in get_payload()["data"]["channels"]}
    assert channels["inapp"] is True
    assert channels["browser"] is False
    assert channels["email"] is False
    assert channels["messenger"] is False
