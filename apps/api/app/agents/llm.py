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
    intent: Literal["query", "analysis", "order", "result", "other"]
    query_kind: Literal["balance", "price", "orders"] | None = Field(
        default=None, description="intent가 query일 때만. balance: 잔고·보유 종목 / price: 현재가 / orders: 오늘 주문 내역"
    )
    stock_name: str | None = Field(default=None, description="요청에 나온 종목 이름이나 코드 그대로. 없으면 null")


UNDERSTAND_PROMPT = """너는 주식 앱의 요청 분석기다.

1. 최근 대화를 보고 요청 속 "그거", "그 종목", "아까 거" 같은 말을 실제 이름으로 바꿔 query에 써라.
   무엇을 가리키는지 확실하지 않으면 바꾸지 마라. 요청의 뜻을 바꾸거나 내용을 더하지 마라.
2. 요청을 하나로 분류하라.
- query: 읽기만 하는 조회. 잔고, 보유 종목, 현재가, 오늘 주문 내역. 예) "잔고 보여줘", "삼성전자 얼마야?"
- analysis: 사도 되는지, 어떤지 판단을 묻는 요청. 예) "삼성전자 사도 돼?", "SK하이닉스 어때?"
- order: 사거나 팔라는 지시. 예) "SK하이닉스 4주 사줘", "삼성전자 다 팔아"
- result: 앞서 한 주문의 결과를 묻는 요청. 예) "아까 주문 체결됐어?"
- other: 주식 앱 업무가 아닌 것
3. query면 query_kind를 채워라. 종목이 나오면 stock_name에 사용자가 말한 그대로 써라. 지어내지 마라.

최근 대화:
{history}"""


def understand(query: str, history: list) -> Understood:
    lines = [f"사용자: {turn['request']}\n답: {turn['answer']}" for turn in history] or ["(없음)"]
    return ask(Understood, UNDERSTAND_PROMPT.format(history="\n".join(lines)), query)
