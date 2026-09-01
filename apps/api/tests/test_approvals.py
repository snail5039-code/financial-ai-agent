from fastapi.testclient import TestClient

from app.main import create_app


def new_client() -> TestClient:
    return TestClient(create_app())


def test_list_returns_all_orders_pending_initially() -> None:
    response = new_client().get("/api/approvals")

    assert response.status_code == 200
    payload = response.json()
    assert payload["isMock"] is True
    assert payload["paperOnly"] is True
    assert payload["executed"] is False
    assert payload["externalConnections"] == 0

    orders = payload["data"]["orders"]
    assert len(orders) == 4
    assert all(order["decisionStatus"] == "pending" for order in orders)
    assert all(order["decidedAt"] is None for order in orders)


def test_order_amount_equals_quantity_times_price() -> None:
    orders = new_client().get("/api/approvals").json()["data"]["orders"]

    for order in orders:
        assert order["amount"] == order["quantity"] * order["price"], order["id"]


def test_approve_transitions_status_and_sets_decided_at() -> None:
    client = new_client()

    response = client.post("/api/approvals/DEC-1042/approve")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["decisionStatus"] == "approved"
    assert payload["data"]["decidedAt"]
    # Approving never means an order was actually placed.
    assert payload["executed"] is False
    assert payload["paperOnly"] is True

    listed = client.get("/api/approvals").json()["data"]["orders"]
    updated = next(o for o in listed if o["id"] == "DEC-1042")
    assert updated["decisionStatus"] == "approved"


def test_reject_transitions_status() -> None:
    client = new_client()

    response = client.post("/api/approvals/DEC-1043/reject")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["decisionStatus"] == "rejected"
    assert payload["data"]["decidedAt"]
    assert payload["executed"] is False


def test_approve_unknown_id_returns_404() -> None:
    response = new_client().post("/api/approvals/DEC-9999/approve")

    assert response.status_code == 404


def test_approve_twice_returns_409_conflict() -> None:
    client = new_client()
    client.post("/api/approvals/DEC-1042/approve")

    response = client.post("/api/approvals/DEC-1042/approve")

    assert response.status_code == 409
    assert "DEC-1042" in response.json()["detail"]


def test_reject_after_approve_returns_409_conflict() -> None:
    client = new_client()
    client.post("/api/approvals/DEC-1044/approve")

    response = client.post("/api/approvals/DEC-1044/reject")

    assert response.status_code == 409


def test_other_orders_are_unaffected_by_one_decision() -> None:
    client = new_client()

    client.post("/api/approvals/DEC-1042/approve")

    orders = client.get("/api/approvals").json()["data"]["orders"]
    others = [o for o in orders if o["id"] != "DEC-1042"]
    assert all(o["decisionStatus"] == "pending" for o in others)


def test_store_state_is_isolated_per_app_instance() -> None:
    # Each create_app() call must get its own store — otherwise a module-level
    # singleton would leak approvals between unrelated app instances (and
    # between tests in this same process).
    first_app_client = new_client()
    second_app_client = new_client()

    first_app_client.post("/api/approvals/DEC-1042/approve")

    second_orders = second_app_client.get("/api/approvals").json()["data"]["orders"]
    still_pending = next(o for o in second_orders if o["id"] == "DEC-1042")
    assert still_pending["decisionStatus"] == "pending"


def test_action_envelope_disclaimer_mentions_no_real_order() -> None:
    payload = new_client().post("/api/approvals/DEC-1045/approve").json()

    assert "실제 주문" in payload["disclaimer"]
