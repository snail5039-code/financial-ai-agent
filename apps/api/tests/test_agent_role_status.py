from fastapi.testclient import TestClient

from app.main import create_app


def get_payload() -> dict:
    client = TestClient(create_app())
    response = client.get("/api/agent-role-status")
    assert response.status_code == 200
    return response.json()


def test_envelope_carries_safety_flags() -> None:
    payload = get_payload()
    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0


def test_returns_four_roles() -> None:
    roles = get_payload()["data"]["roles"]
    assert len(roles) == 4
    assert {r["id"] for r in roles} == {"proposer", "verifier", "policy", "approver"}
