"""Gemini를 부르는 곳은 이 파일 하나다.

LLM은 분류·값 뽑기만 하고, 답 문장과 숫자는 코드가 만든다 (docs/plan/04-graph-design.md).
자동 테스트는 이 파일의 함수들을 가짜로 바꿔 끼워서 Gemini를 부르지 않는다 (비용 0).
"""

from functools import cache
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app import config


class LLMUnavailable(Exception):
    """Gemini 호출 실패. 가짜 답을 만들지 않고 실패라고 알린다 (NFR-08)."""


@cache
def chat_model() -> ChatGoogleGenerativeAI:
    if not config.GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY가 비어 있습니다 (apps/api/.env)")
    return ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, api_key=config.GEMINI_API_KEY)


def ask[T: BaseModel](schema: type[T], instructions: str, text: str) -> T:
    try:
        return chat_model().with_structured_output(schema).invoke(
            [SystemMessage(content=instructions), HumanMessage(content=text)]
        )
    except LLMUnavailable:
        raise
    except Exception as error:
        raise LLMUnavailable(str(error)) from error


# ---------- rewrite: "그거"를 실제 이름으로 ----------

class RewrittenQuery(BaseModel):
    query: str = Field(description="가리키는 말을 실제 이름으로 바꾼 요청. 바꿀 것이 없으면 그대로")


REWRITE_PROMPT = """너는 주식 앱의 대화 도우미다. 최근 대화를 보고 새 요청 속 "그거", "그 종목", "아까 거" 같은 말을
실제 종목 이름이나 대상으로 바꿔라. 바꿀 말이 없거나 무엇을 가리키는지 확실하지 않으면 새 요청을 그대로 돌려줘라.
요청의 뜻을 바꾸거나 내용을 더하지 마라.

최근 대화:
{history}"""


def rewrite_query(query: str, history: list) -> str:
    lines = [f"사용자: {turn['request']}\n답: {turn['answer']}" for turn in history]
    return ask(RewrittenQuery, REWRITE_PROMPT.format(history="\n".join(lines)), query).query.strip() or query


# ---------- classify: 요청 종류 ----------

class Intent(BaseModel):
    intent: Literal["query", "analysis", "order", "result", "other"]


CLASSIFY_PROMPT = """주식 앱 사용자의 요청을 하나로 분류하라.
- query: 읽기만 하는 조회. 잔고, 보유 종목, 현재가, 오늘 주문 내역. 예) "잔고 보여줘", "삼성전자 얼마야?"
- analysis: 사도 되는지, 어떤지 판단을 묻는 요청. 예) "삼성전자 사도 돼?", "SK하이닉스 어때?"
- order: 사거나 팔라는 지시. 예) "SK하이닉스 4주 사줘", "삼성전자 다 팔아"
- result: 앞서 한 주문의 결과를 묻는 요청. 예) "아까 주문 체결됐어?"
- other: 주식 앱 업무가 아닌 것"""


def classify_intent(query: str) -> str:
    return ask(Intent, CLASSIFY_PROMPT, query).intent


# ---------- extract_query: 무엇을 조회할지 ----------

class QueryTarget(BaseModel):
    kind: Literal["balance", "price", "orders"] = Field(
        description="balance: 잔고·보유 종목 / price: 종목 현재가 / orders: 오늘 주문 내역"
    )
    stock_name: str | None = Field(default=None, description="price일 때 사용자가 말한 종목 이름이나 코드. 없으면 null")


EXTRACT_QUERY_PROMPT = "주식 앱 조회 요청에서 무엇을 볼지 뽑아라. 종목 이름은 사용자가 말한 그대로 쓰고 지어내지 마라."


def extract_query(query: str) -> QueryTarget:
    return ask(QueryTarget, EXTRACT_QUERY_PROMPT, query)
