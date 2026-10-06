"""전체 그래프 (1단 supervisor, docs/plan/04-graph-design.md 1장).

    START → understand ─┬─ query          → 조회 그래프 (agents/query.py)
                        ├─ analysis       → 분석 그래프 (agents/analysis.py)
                        ├─ order/result   → not_ready (5단계에서 연결)
                        └─ other          → guide

understand는 Gemini 한 번으로 "그거" 풀기(rewrite) + 분류(classify) + 조회 대상 뽑기를 한다 (속도 때문에 합침).
새 요청일 때만 지난다. 멈춤(question·fetch)의 답은 멈춘 노드에서 이어가므로 여기를 지나지 않는다.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agents import llm
from app.agents.analysis import build_analysis_graph
from app.agents.query import build_query_graph
from app.agents.state import Context, InvestState

GUIDE_MESSAGE = (
    "이렇게 말해 보세요.\n"
    "- 잔고 보여줘\n"
    "- 삼성전자 얼마야?\n"
    "- 오늘 주문 내역 보여줘\n"
    "- 삼성전자 사도 돼?"
)
NOT_READY_MESSAGE = "주문과 주문 결과 확인은 아직 준비 중이에요. 지금은 잔고·시세·주문 내역 조회와 종목 분석을 할 수 있어요."


def understand_node(state: InvestState) -> dict:
    result = llm.understand(state["query"], state.get("history") or [])
    intent = result.intent
    if intent == "query" and result.query_kind is None:
        intent = "other"  # 무엇을 조회할지 모르면 할 수 있는 일을 안내한다
    return {"query": result.query, "intent": intent, "query_kind": result.query_kind, "stock_name": result.stock_name}


def route_by_intent(state: InvestState) -> str:
    return {"query": "query", "analysis": "analysis", "other": "guide"}.get(state["intent"], "not_ready")


def not_ready_node(state: InvestState) -> dict:
    return {"answer": NOT_READY_MESSAGE}


def guide_node(state: InvestState) -> dict:
    return {"answer": GUIDE_MESSAGE}


def build_graph(checkpointer: BaseCheckpointSaver):
    builder = StateGraph(InvestState, context_schema=Context)
    builder.add_node("understand", understand_node)
    builder.add_node("query", build_query_graph())  # 조회 그래프를 노드로 넣는다
    builder.add_node("analysis", build_analysis_graph())
    builder.add_node("not_ready", not_ready_node)
    builder.add_node("guide", guide_node)

    builder.add_edge(START, "understand")
    builder.add_conditional_edges("understand", route_by_intent, ["query", "analysis", "not_ready", "guide"])
    for node in ("query", "analysis", "not_ready", "guide"):
        builder.add_edge(node, END)
    return builder.compile(checkpointer=checkpointer)
