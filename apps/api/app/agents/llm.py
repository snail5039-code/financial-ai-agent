"""Gemini를 부르는 곳은 이 파일 하나다.

LLM은 분류·값 뽑기만 하고, 답 문장과 숫자는 코드가 만든다 (docs/plan/04-graph-design.md).
자동 테스트는 이 파일의 함수들을 가짜로 바꿔 끼워서 Gemini를 부르지 않는다 (비용 0).
"""

from functools import cache
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import BaseModel, Field

from app import config
from app.agents.schemas import ProposalDraft, ReviewDraft, VerificationDraft


class LLMUnavailable(Exception):
    """Gemini 호출 실패. 가짜 답을 만들지 않고 실패라고 알린다 (NFR-08)."""


@cache
def chat_model(thinking_level: str) -> ChatGoogleGenerativeAI:
    """thinking_level: Gemini 3가 답하기 전에 생각하는 정도 (minimal / low / medium / high).
    분류처럼 쉬운 일은 minimal로 빠르게 한다. 투자 판단(4단계)은 더 높게 쓸 수 있다."""
    if not config.GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY가 비어 있습니다 (apps/api/.env)")
    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL, api_key=config.GEMINI_API_KEY, thinking_level=thinking_level
    )


def ask[T: BaseModel](schema: type[T], instructions: str, text: str, thinking_level: str = "minimal") -> T:
    try:
        return chat_model(thinking_level).with_structured_output(schema).invoke(
            [SystemMessage(content=instructions), HumanMessage(content=text)]
        )
    except LLMUnavailable:
        raise
    except Exception as error:
        raise LLMUnavailable(str(error)) from error


# ---------- 공시 검색용 임베딩 ----------
# 768차원: DB 칸(vector(768))과 같아야 한다. Gemini 임베딩이 정해 둔 줄임 크기 중 하나

EMBEDDING_DIMENSIONS = 768


@cache
def embedder() -> GoogleGenerativeAIEmbeddings:
    if not config.GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY가 비어 있습니다 (apps/api/.env)")
    return GoogleGenerativeAIEmbeddings(model=config.GEMINI_EMBEDDING_MODEL, google_api_key=config.GEMINI_API_KEY,
                                        output_dimensionality=EMBEDDING_DIMENSIONS)


def embed_documents(texts: list[str]) -> list[list[float]]:
    try:
        return embedder().embed_documents(texts, task_type="RETRIEVAL_DOCUMENT")
    except Exception as error:
        raise LLMUnavailable(str(error)) from error


def embed_query(text: str) -> list[float]:
    try:
        return embedder().embed_query(text, task_type="RETRIEVAL_QUERY")
    except Exception as error:
        raise LLMUnavailable(str(error)) from error


# ---------- understand: 요청 이해 (한 번의 호출) ----------
# "그거" 풀기, 요청 분류, 조회 대상 뽑기를 한 번에 한다.
# 따로 부르면 2~3번 호출로 6~10초 걸려서 합쳤다 (2026-10-05 측정: 한 번에 약 1.4초).

class Understood(BaseModel):
    query: str = Field(description="가리키는 말(그거, 그 종목, 아까 거)을 실제 이름으로 바꾼 요청. 바꿀 것이 없으면 그대로")
    intent: Literal["query", "analysis", "order", "result", "explain", "history", "other"]
    query_kind: Literal["balance", "price", "orders"] | None = Field(
        default=None, description="intent가 query일 때만. balance: 잔고·보유 종목 / price: 현재가 / orders: 오늘 주문 내역"
    )
    stock_name: str | None = Field(default=None, description="요청에 나온 종목 이름이나 코드 그대로. 없으면 null")
    side: Literal["buy", "sell"] | None = Field(
        default=None, description="order·history일 때만. 사줘·샀어 → buy, 팔아·팔았어 → sell. 말하지 않았으면 null")
    qty: int | None = Field(default=None, description="order일 때 사용자가 말한 주식 수. 말하지 않았으면 null")
    limit_price: int | None = Field(default=None, description="order일 때 사용자가 말한 1주 가격(원). 없으면 null")
    term: str | None = Field(default=None, description="explain일 때만. 뜻을 묻는 용어 그대로 (예: PER, 공매도)")
    period: Literal["today", "week", "month"] | None = Field(
        default=None, description="history일 때만. 오늘 → today, 이번 주·최근 일주일 → week, 이번 달·최근 → month. 없으면 null")
    history_kind: Literal["orders", "rejected"] | None = Field(
        default=None, description="history일 때만. 산 것·판 것·주문 → orders, 반려·검증에서 걸린 것 → rejected. 그 밖은 null")


UNDERSTAND_PROMPT = """너는 주식 앱의 요청 분석기다.

1. 최근 대화를 보고 요청 속 "그거", "그 종목", "아까 거" 같은 말을 실제 이름으로 바꿔 query에 써라.
   무엇을 가리키는지 확실하지 않으면 바꾸지 마라. 요청의 뜻을 바꾸거나 내용을 더하지 마라.
2. 요청을 하나로 분류하라.
- query: 읽기만 하는 조회. 잔고, 보유 종목, 현재가, 오늘 주문 내역. 예) "잔고 보여줘", "삼성전자 얼마야?"
- analysis: 사도 되는지, 어떤지 판단을 묻는 요청. 예) "삼성전자 사도 돼?", "SK하이닉스 어때?"
- order: 사거나 팔라는 지시. 예) "SK하이닉스 4주 사줘", "삼성전자 다 팔아"
- result: 앞서 한 주문의 결과를 묻는 요청. 예) "아까 주문 체결됐어?"
- explain: 투자·금융 용어의 뜻을 묻는 요청. 예) "PER이 뭐야?", "공매도가 뭐야", "부채비율 뜻". term에 용어만 써라
- history: 내가 지난번에 받은 제안·검증 결과·주문 기록을 묻는 요청. 예) "지난번에 SK하이닉스 왜 반려됐지?",
  "이번 달에 뭐 샀지?", "최근 검증에서 걸린 거 보여줘". period·history_kind·side·stock_name을 말한 대로만 채워라.
  방금 한 주문 하나가 체결됐는지 묻는 것은 result다
- other: 주식 앱 업무가 아닌 것
3. query면 query_kind를 채워라. 종목이 나오면 stock_name에 사용자가 말한 그대로 써라. 지어내지 마라.
4. order면 side, qty, limit_price를 사용자가 말한 대로만 채워라. "4주" → qty 4, "7만원에" → limit_price 70000.
   금액으로 말했거나("100만원어치") 말하지 않은 값은 null로 둔다. 추측하지 마라.

최근 대화:
{history}"""


def understand(query: str, history: list) -> Understood:
    lines = [f"사용자: {turn['request']}\n답: {turn['answer']}" for turn in history] or ["(없음)"]
    return ask(Understood, UNDERSTAND_PROMPT.format(history="\n".join(lines)), query)


# ---------- 투자 AI · 검증 AI (4단계) ----------
# 두 AI는 서로 다른 지시문을 쓰고, 검증 AI는 투자 AI의 입력·지시문을 보지 않는다 (FR-17).
# 무엇을 넘길지는 agents/analysis.py가 정한다. 여기는 부르기만 한다.

INVEST_PROMPT = """너는 한국 주식 앱의 투자 AI다. 주어진 자료만 써서 이 종목에 대한 제안서를 쓴다.

규칙
- 행동(action)은 [허용 행동] 중에서만 고른다.
- 모든 사실(fact)·계산(calc) 근거에는 [자료]의 출처 ID를 단다. 계산 근거에는 [지표]의 지표 ID도 단다.
- 숫자는 [지표]와 [자료]에 있는 값만 쓴다. 직접 계산하거나 지어내지 않는다. 없는 정보는 "미확인"이라고 쓴다.
- 사실, 계산, 추론, 의견을 구분한다. "무조건 오른다", "위험 없다" 같은 표현을 쓰지 않는다.
- 반대 근거와 위험(손실 가능성, 수수료·세금 포함)을 반드시 쓴다.
- 검증 AI의 반박이 있으면 그 점을 고쳐서 다시 쓴다.
- [사용자] 안내를 따른다 (예: 고령이면 불리한 점을 먼저, 고금리 빚이 있으면 빚 상환 안내)."""

VERIFY_PROMPT = """너는 한국 주식 앱의 검증 AI다. 투자 AI가 쓴 제안서를 믿지 말고 원문으로 다시 확인한다.

반드시 확인할 것 (checks에 하나씩 남긴다)
1. 사실·계산 근거마다 출처가 있고, [원문]이 그 문장을 실제로 뒷받침하는가 (target: claim:번호)
2. 근거에 쓴 숫자가 [다시 계산한 지표]와 같은가
3. 자료가 오래되지 않았는가 (target: freshness)
4. 사실·추론·의견을 섞지 않았는가, 지나친 확신은 없는가
5. 반대 근거와 위험을 빠뜨리지 않았는가 (target: counter_arguments)
6. [사용자] 성향과 맞는가 (target: risk_fit)
[코드 검사]에 fail이 있으면 승인하지 않는다.

판정
- approve: 문제 없음 / conditional: 조건을 지키면 괜찮음 (conditions에 조건) / reject: 고쳐야 함 (challenges에 반박)
- user_judgement: 자료가 부족하거나 서로 맞지 않아 AI가 판단하기 어려움
투자 AI와 생각이 다른 점은 disagreements에 쓴다. 사용자에게 그대로 보여준다."""


def write_proposal(context: str) -> ProposalDraft:
    return ask(ProposalDraft, INVEST_PROMPT, context, thinking_level="low")


def verify_proposal(context: str) -> VerificationDraft:
    return ask(VerificationDraft, VERIFY_PROMPT, context, thinking_level="low")


# ---------- 장 마감 회고 · 내일 계획 (12-todo-by-stage.md 2-4b) ----------
# 분석과 같은 규칙: 투자 AI가 쓰고, 검증 AI가 출처 원문을 다시 읽고 판정한다. 주문은 만들지 않는다.

REVIEW_PROMPT = """너는 한국 주식 앱의 투자 AI다. 장이 끝난 뒤 사용자의 오늘 매매를 돌아보고 내일 볼 것을 쓴다.

규칙
- retrospective(오늘 회고): 오늘 산·판 이유([자료]의 제안서 근거)가 오늘 공시·종가와 맞았는지, 한도·규칙을 지켰는지,
  한 종목에 몰렸는지(비중), 수수료·세금 같은 비용을 본다. 오늘 매매가 없으면 그렇다고 쓴다.
- tomorrow(내일 볼 것): [종목]마다 하나. action은 그 종목의 허용 행동 중에서만 고른다. 주문을 만들거나 수량·가격을 정하지 않는다.
- 모든 사실(fact)·계산(calc) 근거에는 [자료]의 출처 ID를 단다. 숫자는 [자료]에 있는 값만 쓴다. 직접 계산하거나 지어내지 않는다.
- [종목]의 위험등급·허용 행동은 앱 규칙이지 근거가 아니다. 근거(reasons)에 쓰지 않는다. 출처 ID는 그 문장이 실제로 들어 있는 자료에만 단다.
- 사실, 계산, 추론, 의견을 구분한다. "무조건 오른다", "위험 없다" 같은 표현을 쓰지 않는다. 없는 정보는 "미확인"이라고 쓴다.
- risks에 손실 가능성과 수수료·세금을 반드시 쓴다.
- 검증 AI의 반박이 있으면 그 점을 고쳐서 다시 쓴다.
- [사용자] 안내를 따른다."""

REVIEW_VERIFY_PROMPT = """너는 한국 주식 앱의 검증 AI다. 투자 AI가 쓴 장 마감 회고·내일 계획을 믿지 말고 원문으로 다시 확인한다.

반드시 확인할 것 (checks에 하나씩 남긴다)
1. 사실·계산 근거마다 출처가 있고, [원문]이 그 문장을 실제로 뒷받침하는가 (target: 근거 번호 그대로)
2. 숫자가 [원문]과 같은가
3. 사실·추론·의견을 섞지 않았는가, 지나친 확신은 없는가
4. 손실 가능성·수수료·세금을 빠뜨리지 않았는가 (target: risks)
5. [사용자] 성향과 맞는가 (target: risk_fit)
[코드 검사]에 fail이 있으면 승인하지 않는다.

판정
- approve: 문제 없음 / conditional: 조건을 지키면 괜찮음 (conditions에 조건) / reject: 고쳐야 함 (challenges에 반박)
- user_judgement: 자료가 부족하거나 서로 맞지 않아 AI가 판단하기 어려움
투자 AI와 생각이 다른 점은 disagreements에 쓴다. 사용자에게 그대로 보여준다."""


def write_review(context: str) -> ReviewDraft:
    return ask(ReviewDraft, REVIEW_PROMPT, context, thinking_level="low")


def verify_review(context: str) -> VerificationDraft:
    return ask(VerificationDraft, REVIEW_VERIFY_PROMPT, context, thinking_level="low")


# ---------- 처리안 수정 ("5주만", "6만9천원에") ----------

class OrderEdit(BaseModel):
    qty: int | None = Field(default=None, description="바꾼 주식 수. 말하지 않았으면 null")
    limit_price: int | None = Field(default=None, description="바꾼 1주 가격(원). 말하지 않았으면 null")


EDIT_PROMPT = """주식 주문 처리안을 고치는 말에서 바꾸려는 수량과 가격만 뽑아라. 말하지 않은 값은 null.
지금 처리안: {order}"""


def parse_order_edit(text: str, order: str) -> OrderEdit:
    return ask(OrderEdit, EDIT_PROMPT.format(order=order), text)
