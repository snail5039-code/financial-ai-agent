from fastapi.testclient import TestClient

from app.main import create_app


def get_payload() -> dict:
    client = TestClient(create_app())
    response = client.get("/api/company-detail")
    assert response.status_code == 200
    return response.json()


def test_envelope_carries_safety_flags() -> None:
    payload = get_payload()
    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0


def test_returns_twelve_chart_points_and_six_metrics() -> None:
    data = get_payload()["data"]
    assert len(data["chart"]) == 12
    assert len(data["metrics"]) == 6
    assert len(data["evidence"]) == 6
    assert len(data["filings"]) == 3


def test_price_panel_agrees_with_dashboard_holding() -> None:
    client = TestClient(create_app())
    price = client.get("/api/company-detail").json()["data"]["price"]
    holding = next(
        h for h in client.get("/api/dashboard").json()["data"]["holdings"] if h["code"] == "005930"
    )

    assert price["quantity"] == holding["quantity"]
    assert price["averagePrice"] == holding["averagePrice"]
    assert price["currentPrice"] == holding["currentPrice"]
    assert price["value"] == holding["value"]
    assert price["profit"] == holding["profit"]
    assert price["weight"] == holding["weight"]
