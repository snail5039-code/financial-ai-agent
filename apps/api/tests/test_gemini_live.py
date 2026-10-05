"""실제 Gemini로 분류·값 뽑기가 맞는지 확인한다. 비용이 들어서 기본 테스트에서는 빠진다.

실행: uv run pytest -m gemini
"""

import pytest

from app import config
from app.agents import llm

pytestmark = [
    pytest.mark.gemini,
    pytest.mark.skipif(not config.GEMINI_API_KEY, reason="GEMINI_API_KEY 없음"),
]


@pytest.mark.parametrize(
    "text, intent",
    [
        ("잔고 보여줘", "query"),
        ("내 계좌에 돈 얼마 있어?", "query"),
        ("삼성전자 지금 얼마야?", "query"),
        ("오늘 주문한 거 보여줘", "query"),
        ("SK하이닉스 사도 될까?", "analysis"),
        ("카카오 요즘 어때?", "analysis"),
        ("SK하이닉스 4주 사줘", "order"),
        ("삼성전자 10주 팔아줘", "order"),
        ("아까 주문 체결됐어?", "result"),
        ("오늘 날씨 어때?", "other"),
    ],
)
def test_classify(text: str, intent: str) -> None:
    assert llm.classify_intent(text) == intent


@pytest.mark.parametrize(
    "text, kind, stock_name",
    [
        ("잔고 보여줘", "balance", None),
        ("삼성전자 지금 얼마야?", "price", "삼성전자"),
        ("오늘 주문 내역 보여줘", "orders", None),
    ],
)
def test_extract_query(text: str, kind: str, stock_name: str | None) -> None:
    target = llm.extract_query(text)
    assert target.kind == kind
    assert target.stock_name == stock_name


def test_rewrite_resolves_reference() -> None:
    history = [{"request": "삼성전자 얼마야?", "answer": "삼성전자(005930) 현재가 71,200원"}]
    assert "삼성전자" in llm.rewrite_query("그거 다시 알려줘", history)
