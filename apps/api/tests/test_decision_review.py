from fastapi.testclient import TestClient

from app.main import create_app


def get_payload() -> dict:
    client = TestClient(create_app())
    response = client.get("/api/decision-review")
    assert response.status_code == 200
    return response.json()


def test_envelope_carries_safety_flags() -> None:
    payload = get_payload()
    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0


def test_returns_four_decisions_with_valid_outcomes() -> None:
    decisions = get_payload()["data"]["decisions"]
    assert len(decisions) == 4
    for row in decisions:
        assert row["decision"] in ("승인", "반려", "보류")
        assert not row["linkPage"].startswith("http")
