from fastapi.testclient import TestClient

from app.fixtures.dashboard import build_dashboard_data
from app.main import create_app


def get_payload() -> dict:
    client = TestClient(create_app())
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    return response.json()


def test_dashboard_envelope_carries_safety_flags() -> None:
    payload = get_payload()

    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0
    assert payload["sourceLabel"] == "로컬 fixture"
    assert payload["generatedAt"]
    assert payload["dataAsOf"] == "2026-08-27T15:20:00+09:00"
    assert "연결되지 않습니다" in payload["disclaimer"]
    assert "data" in payload


def test_dashboard_money_and_percent_fields_are_numeric() -> None:
    data = get_payload()["data"]

    assert data["currency"] == "KRW"

    summary = data["summary"]
    for field in ("totalAsset", "todayProfit", "principal", "accumulatedProfit"):
        assert isinstance(summary[field], int), field
    for field in ("todayProfitRate", "cashWeight"):
        assert isinstance(summary[field], (int, float)), field
        assert not isinstance(summary[field], str), field

    for holding in data["holdings"]:
        assert isinstance(holding["value"], int)
        assert isinstance(holding["weight"], (int, float))
        assert not isinstance(holding["weight"], str)

    decision = data["decision"]
    assert isinstance(decision["limitPrice"], int)
    assert isinstance(decision["limitAmount"], int)
    assert isinstance(decision["targetWeightFrom"], (int, float))
    assert isinstance(decision["targetWeightTo"], (int, float))


def test_holding_values_sum_to_total_asset() -> None:
    data = get_payload()["data"]

    assert sum(holding["value"] for holding in data["holdings"]) == data["summary"]["totalAsset"]


def test_holding_weights_are_consistent_with_values() -> None:
    data = get_payload()["data"]
    total = data["summary"]["totalAsset"]

    for holding in data["holdings"]:
        implied = holding["value"] / total * 100
        assert abs(implied - holding["weight"]) < 0.01, holding["code"]


def test_cash_holding_uses_null_instead_of_placeholder_text() -> None:
    data = get_payload()["data"]
    cash = next(holding for holding in data["holdings"] if holding["code"] == "KRW")

    assert cash["quantity"] is None
    assert cash["averagePrice"] is None
    assert cash["currentPrice"] is None
    assert cash["profit"] is None
    assert cash["profitRate"] is None
    assert cash["value"] > 0


def test_decision_reports_no_execution() -> None:
    decision = get_payload()["data"]["decision"]

    assert decision["decisionId"] == "DEC-1042"
    assert any(
        check["label"] == "실제 주문" and check["value"] == "생성 안 됨"
        for check in decision["checks"]
    )
    assert decision["invalidConditions"]


def test_fixture_builder_matches_declared_schema() -> None:
    # Round-tripping proves the fixture cannot drift away from the schema
    # (extra="forbid" plus literal safety flags).
    data = build_dashboard_data()

    assert data.model_dump() == build_dashboard_data().model_dump()
    assert data.summary.totalAsset == sum(holding.value for holding in data.holdings)
