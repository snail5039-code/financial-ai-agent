"""공공데이터 시세 조회: 시간 초과는 다시 시도하고, 계속 실패하면 오류를 그대로 낸다."""

import httpx
import pytest

from app.integrations import market_data


class Ok:
    status_code = 200
    text = ""

    def json(self):
        return {"response": {"header": {"resultCode": "00", "resultMsg": "OK"}, "body": {"items": {}}}}


def test_retries_timeout_then_succeeds(monkeypatch) -> None:
    calls = []

    def fake_get(*a, **k):
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ReadTimeout("느림")
        return Ok()

    monkeypatch.setattr(market_data.httpx, "get", fake_get)
    assert market_data._page("k", {}) == {"items": {}} and len(calls) == 3


def test_gives_up_after_retries(monkeypatch) -> None:
    def fake_get(*a, **k):
        raise httpx.ReadTimeout("느림")

    monkeypatch.setattr(market_data.httpx, "get", fake_get)
    with pytest.raises(httpx.ReadTimeout):
        market_data._page("k", {})
