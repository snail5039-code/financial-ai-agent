"""멈춤(interrupt) 형식과 답 검사 (docs/plan/06-api-spec.md 3장).

서버 그래프가 멈추는 곳은 question / fetch / approval / execute 네 가지뿐이다.
멈춤에 대한 답은 그래프에 넣기 전에 chat 라우터가 여기 모델로 검사한다. 틀리면 그래프는 멈춘 채로 남는다.
모든 모델은 정해진 칸 외에는 받지 않는다 (extra="forbid"). 계좌번호 같은 칸이 섞여 오면 거부한다 (NFR-01).
"""

from datetime import datetime, timedelta
from typing import Annotated

from langgraph.types import interrupt
from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.clock import KST

MAX_KRW = 10**15
STOCK_CODE_PATTERN = r"^[0-9A-Z]{6}$"


def not_in_future(value: datetime) -> datetime:
    # 폰 시계가 조금 빠를 수 있어서 5분까지는 받는다
    if value > datetime.now(KST) + timedelta(minutes=5):
        raise ValueError("조회 시각이 미래예요")
    return value


FetchedAt = Annotated[AwareDatetime, AfterValidator(not_in_future)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Holding(Strict):
    stock_code: str = Field(pattern=STOCK_CODE_PATTERN)
    stock_name: str = Field(min_length=1, max_length=100)
    qty: int = Field(gt=0)
    avg_price: int = Field(ge=0, le=MAX_KRW)


class Balance(Strict):
    """폰이 증권사에서 조회한 계좌 요약. 계좌번호는 없다. POST /api/snapshot도 이 형식을 쓴다."""

    cash_krw: int = Field(ge=0, le=MAX_KRW)
    holdings: list[Holding] = Field(max_length=200)
    fetched_at: FetchedAt


class Price(Strict):
    stock_code: str = Field(pattern=STOCK_CODE_PATTERN)
    price: int = Field(gt=0, le=MAX_KRW)
    as_of: FetchedAt


class FetchAnswer(Strict):
    """fetch 멈춤에 대한 폰의 답: 조회 결과 또는 실패 사유 중 하나."""

    balance: Balance | None = None
    prices: list[Price] | None = Field(default=None, max_length=20)
    error: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def check_result_or_error(self) -> "FetchAnswer":
        has_result = self.balance is not None or self.prices is not None
        if has_result == (self.error is not None):
            raise ValueError("조회 결과(balance, prices)나 실패 사유(error) 중 하나만 보내 주세요")
        return self


class QuestionAnswer(Strict):
    """question 멈춤에 대한 사용자의 답: 글로 답하거나 후보 중 하나를 고른다."""

    text: str | None = Field(default=None, min_length=1, max_length=200)
    choice_id: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def check_one_answer(self) -> "QuestionAnswer":
        if (self.text is None) == (self.choice_id is None):
            raise ValueError("text나 choice_id 중 하나만 보내 주세요")
        return self


# approval · execute 답 형식은 5단계(주문 그래프)에서 더한다
ANSWER_MODELS: dict[str, type[Strict]] = {"question": QuestionAnswer, "fetch": FetchAnswer}


def pause(kind: str, **data) -> dict:
    """그래프를 멈추고 앱·웹의 답을 기다린다. 답은 chat 라우터가 이미 검사한 dict로 돌아온다.

    LangGraph는 이어서 진행할 때 이 노드를 처음부터 다시 실행하므로, 멈추기 전에는 LLM 호출 같은 일을 하지 않는다.
    """
    return interrupt({"kind": kind, **data})
