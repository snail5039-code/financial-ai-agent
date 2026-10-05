"""전체 그래프 (1단 supervisor, docs/plan/04-graph-design.md 1장).

    START → rewrite → classify ─┬─ query          → 조회 그래프 (agents/query.py)
                                ├─ analysis/order/result → not_ready (4·5단계에서 연결)
                                └─ other          → guide

rewrite는 새 요청일 때만 지난다. 멈춤(question·fetch)의 답은 멈춘 노드에서 이어가므로 여기를 지나지 않는다.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agents import llm
from app.agents.query import build_query_graph
from app.agents.state import Context, InvestState

GUIDE_MESSAGE = (
    "이렇게 말해 보세요.\n"
    "- 잔고 보여줘\n"
    "- 삼성전자 얼마야? (앱에서)\n"
    "- 오늘 주문 내역 보여줘"
)
NOT_READY_MESSAGE = "종목 분석, 주문, 주문 결과 확인은 아직 준비 중이에요. 지금은 잔고·시세·주문 내역 조회만 할 수 있어요."


def rewrite_node(state: InvestState) -> dict:
    """최근 대화를 보고 "그거", "그 종목"을 실제 이름으로 바꾼다 (FR-12). 대화가 없으면 LLM을 부르지 않는다."""
    if not state.get("history"):
        return {}
    return {"query": llm.rewrite_query(state["query"], state["history"])}


def classify_node(state: InvestState) -> dict:
    return {"intent": llm.classify_intent(state["query"])}


def route_by_intent(state: InvestState) -> str:
    return {"query": "query", "other": "guide"}.get(state["intent"], "not_ready")


def not_ready_node(state: InvestState) -> dict:
    return {"answer": NOT_READY_MESSAGE}


def guide_node(state: InvestState) -> dict:
    return {"answer": GUIDE_MESSAGE}


def build_graph(checkpointer: BaseCheckpointSaver):
    builder = StateGraph(InvestState, context_schema=Context)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("classify", classify_node)
    builder.add_node("query", build_query_graph())  # 조회 그래프를 노드로 넣는다
    builder.add_node("not_ready", not_ready_node)
    builder.add_node("guide", guide_node)

    builder.add_edge(START, "rewrite")
    builder.add_edge("rewrite", "classify")
    builder.add_conditional_edges("classify", route_by_intent, ["query", "not_ready", "guide"])
    for node in ("query", "not_ready", "guide"):
        builder.add_edge(node, END)
    return builder.compile(checkpointer=checkpointer)
