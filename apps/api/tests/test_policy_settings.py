from fastapi.testclient import TestClient

from app.main import create_app


def get_payload() -> dict:
    client = TestClient(create_app())
    response = client.get("/api/policy-settings")
    assert response.status_code == 200
    return response.json()


def test_envelope_carries_safety_flags() -> None:
    payload = get_payload()
    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0


def test_returns_six_number_rules_and_four_checks() -> None:
    data = get_payload()["data"]
    assert len(data["numberRules"]) == 6
    assert len(data["checks"]) == 4
    for rule in data["numberRules"]:
        # `value` is deliberately a string (bound to a text input); it must
        # still parse as a number within the rule's own min/max.
        assert rule["min"] <= float(rule["value"]) <= rule["max"]


def test_preview_agrees_with_dashboard_and_approvals_on_dec_1042() -> None:
    client = TestClient(create_app())
    preview = client.get("/api/policy-settings").json()["data"]["preview"]
    dashboard = client.get("/api/dashboard").json()["data"]["decision"]
    order = next(
        o for o in client.get("/api/approvals").json()["data"]["orders"] if o["id"] == "DEC-1042"
    )

    assert preview["decisionId"] == "DEC-1042"
    assert preview["amount"] == dashboard["limitAmount"] == order["amount"]
    assert preview["nextWeight"] == dashboard["targetWeightTo"]
