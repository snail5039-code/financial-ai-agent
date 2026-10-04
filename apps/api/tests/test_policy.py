import pytest

MIDDLE_ANSWERS = [3, 3, 3, 3, 3]  # 15점 → 3단계 위험중립형 (100만 / 200만 / 30%)
VALID_POLICY = {"max_order_krw": 500_000, "max_daily_krw": 1_000_000, "max_weight_pct": 20}


def take_survey(client, user, answers=MIDDLE_ANSWERS):
    return client.put("/api/profile", headers=user["headers"], json={"answers": answers})


def test_profile_and_policy_need_login(client) -> None:
    assert client.get("/api/profile").status_code == 401
    assert client.put("/api/policy", json=VALID_POLICY).status_code == 401


def test_policy_before_survey_is_409(client, user) -> None:
    assert client.get("/api/profile", headers=user["headers"]).status_code == 404
    assert client.get("/api/policy", headers=user["headers"]).status_code == 409
    assert client.put("/api/policy", headers=user["headers"], json=VALID_POLICY).status_code == 409


def test_survey_sets_level_and_default_policy(client, user) -> None:
    response = take_survey(client, user)

    assert response.status_code == 200
    body = response.json()
    assert (body["risk_level"], body["label"]) == (3, "위험중립형")
    assert body["policy"]["max_order_krw"] == 1_000_000
    assert body["policy"]["max_daily_krw"] == 2_000_000
    assert body["policy"]["max_weight_pct"] == 30
    assert body["policy"]["fee_rate_pct"] is None
    assert body["policy"]["warnings"] == []
    assert client.get("/api/profile", headers=user["headers"]).json()["answers"] == MIDDLE_ANSWERS


def test_bad_survey_answers_are_422(client, user) -> None:
    assert take_survey(client, user, [3, 3, 3]).status_code == 422
    assert take_survey(client, user, [3, 3, 3, 3, 9]).status_code == 422


def test_resurvey_lowers_limits_but_never_raises_them(client, user) -> None:
    take_survey(client, user)  # 3단계
    client.put("/api/policy", headers=user["headers"], json={**VALID_POLICY, "max_order_krw": 100_000})

    lower = take_survey(client, user, [1, 1, 1, 1, 1]).json()["policy"]  # 1단계: 30만 / 50만 / 20%
    assert (lower["max_order_krw"], lower["max_daily_krw"]) == (100_000, 500_000)

    higher = take_survey(client, user, [5, 5, 5, 5, 5]).json()["policy"]  # 5단계여도 그대로
    assert (higher["max_order_krw"], higher["max_daily_krw"]) == (100_000, 500_000)


def test_update_policy_and_fee_rate(client, user) -> None:
    take_survey(client, user)

    response = client.put("/api/policy", headers=user["headers"], json={**VALID_POLICY, "fee_rate_pct": 0.015})

    assert response.status_code == 200
    assert response.json()["max_order_krw"] == 500_000
    assert response.json()["fee_rate_pct"] == 0.015
    assert response.json()["warnings"] == []


def test_limits_above_profile_default_save_with_warning(client, user) -> None:
    take_survey(client, user)

    response = client.put(
        "/api/policy", headers=user["headers"],
        json={"max_order_krw": 1_500_000, "max_daily_krw": 3_000_000, "max_weight_pct": 30},
    )

    assert response.status_code == 200
    assert response.json()["max_order_krw"] == 1_500_000
    assert len(response.json()["warnings"]) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"max_order_krw": 0},
        {"max_order_krw": -1},
        {"max_order_krw": 10**12 + 1},
        {"max_order_krw": 1.5},
        {"max_daily_krw": 400_000},  # 1회 한도(50만)보다 작음
        {"max_weight_pct": 100.01},
        {"max_weight_pct": -1},
        {"max_weight_pct": 10.123},
        {"fee_rate_pct": 1.01},
        {"fee_rate_pct": -0.01},
        {"fee_rate_pct": 0.00001},
    ],
)
def test_policy_rejects_out_of_range(client, user, changes: dict) -> None:
    take_survey(client, user)
    response = client.put("/api/policy", headers=user["headers"], json={**VALID_POLICY, **changes})
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_users_cannot_see_each_others_policy(client, user) -> None:
    take_survey(client, user, [1, 1, 1, 1, 1])
    other = client.post("/api/auth/signup", json={"email": "other-" + user["email"], "password": "pw-other-1", "agreed_terms": True})
    assert other.status_code == 201
    token = client.post("/api/auth/login", json={"email": "other-" + user["email"], "password": "pw-other-1"}).json()["token"]

    response = client.get("/api/policy", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 409  # 다른 사람은 아직 설문 전이라 내 정책이 보이면 안 된다
