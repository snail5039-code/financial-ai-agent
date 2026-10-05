"""모든 그래프가 같이 쓰는 State (docs/plan/04-graph-design.md 7장).

체크포인트(PostgresSaver)가 thread_id마다 State를 저장하므로 턴이 바뀌어도 값이 남는다.
그래서 새 요청을 시작할 때 new_request()로 이번 업무 칸을 비운다.
지금은 3단계(조회)에 필요한 칸만 있다. 분석·주문 칸은 4·5단계에서 더한다.
"""

from dataclasses import dataclass
from typing import TypedDict


@dataclass
class Context:
    """그래프 실행마다 넘기는 값. State와 달리 체크포인트에 저장되지 않는다 (DB 주소에 비밀번호가 있어서)."""

    database_url: str


class InvestState(TypedDict, total=False):
    # 공통
    user_id: str
    thread_id: str
    client: str              # app / web. 웹은 증권사 조회(fetch)를 못 한다
    query: str               # 이번 입력 ("그거"를 풀었으면 푼 문장)
    history: list            # 최근 대화 [{request, answer}, ...] (최대 5턴)
    intent: str              # query / analysis / order / result / other
    answer: str              # 사용자에게 보여줄 답

    # 성향 (docs/plan/09-investor-profile.md). 3단계에서는 담아 두기만 하고 4·5단계에서 쓴다
    mode: str                # general / custom
    risk_level: int | None
    flags: list

    # 조회
    query_kind: str          # balance / price / orders
    stock_name: str | None   # 사용자가 말한 종목 이름
    stock_code: str | None   # 찾아낸 종목 코드
    snapshot: dict | None    # 계좌: cash_krw, holdings, fetched_at, source(app / server)
    prices: list | None      # [{stock_code, price, as_of}]


def new_request(query: str, history: list, profile: dict) -> dict:
    """새 요청의 시작값. 지난 업무의 값이 섞이지 않게 비운다. 대화 ID·사용자 정보는 호출하는 쪽이 넣는다."""
    return {
        "query": query, "history": history, "intent": None, "answer": None,
        "mode": profile["mode"], "risk_level": profile.get("risk_level"), "flags": profile.get("flags", []),
        "query_kind": None, "stock_name": None, "stock_code": None, "snapshot": None, "prices": None,
    }
