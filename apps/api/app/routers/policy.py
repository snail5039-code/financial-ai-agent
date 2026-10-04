"""투자성향 설문과 투자 정책 (FR-02, FR-03, FR-07 ~ FR-07b)."""

from decimal import Decimal
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field, model_validator

from app.db import Conn, audit
from app.functions.profile import DEFAULT_POLICIES, LABELS, lowered_policy, policy_warnings, risk_level
from app.routers.auth import UserId

router = APIRouter(prefix="/api", tags=["profile", "policy"])

# 1조 원. bigint 범위를 넘는 값이 DB까지 가지 않게 막는다
MAX_KRW = 10**12
LIMIT_FIELDS = ("max_order_krw", "max_daily_krw", "max_weight_pct")


class ProfileRequest(BaseModel):
    answers: list[int]  # 설문 답 5개, 각각 1~5점 (app/functions/profile.py)


class PolicyRequest(BaseModel):
    max_order_krw: int = Field(gt=0, le=MAX_KRW)
    max_daily_krw: int = Field(gt=0, le=MAX_KRW)
    max_weight_pct: Decimal = Field(ge=0, le=100, decimal_places=2)
    fee_rate_pct: Decimal | None = Field(default=None, ge=0, le=1, decimal_places=4)

    @model_validator(mode="after")
    def check_daily_covers_order(self) -> "PolicyRequest":
        if self.max_daily_krw < self.max_order_krw:
            raise ValueError("1일 한도는 1회 한도보다 작을 수 없어요")
        return self


def load_policy(conn: psycopg.Connection, user_id: UUID) -> dict:
    """정책과 성향 단계를 함께 읽는다. 설문 전이면 409."""
    row = conn.execute(
        "SELECT p.*, ip.risk_level FROM policies p JOIN investor_profiles ip USING (user_id)"
        " WHERE p.user_id = %s",
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(409, "성향 설문을 먼저 해 주세요")
    return row


def as_json_numbers(values: dict) -> dict:
    """비율(Decimal)을 JSON 숫자로 내보낸다. FastAPI는 Decimal을 문자열로 바꾸기 때문이다. 계산은 Decimal로 한다."""
    return {key: float(value) if isinstance(value, Decimal) else value for key, value in values.items()}


def policy_response(row: dict) -> dict:
    level = row["risk_level"]
    return {
        **as_json_numbers({key: row[key] for key in (*LIMIT_FIELDS, "fee_rate_pct")}),
        "updated_at": row["updated_at"],
        "risk_level": level,
        "default_policy": as_json_numbers(DEFAULT_POLICIES[level]),
        "warnings": policy_warnings(row, level),
    }


@router.get("/profile")
def get_profile(conn: Conn, user_id: UserId) -> dict:
    row = conn.execute(
        "SELECT risk_level, answers, updated_at FROM investor_profiles WHERE user_id = %s", (user_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "아직 성향 설문을 하지 않았어요")
    return {**row, "label": LABELS[row["risk_level"]]}


@router.put("/profile")
def put_profile(body: ProfileRequest, conn: Conn, user_id: UserId) -> dict:
    """설문 답 → 성향 단계. 처음이면 기본 한도로 정책을 만들고, 다시 하면 한도를 올리지 않고 내리기만 한다."""
    try:
        level = risk_level(body.answers)
    except ValueError as error:
        raise HTTPException(422, str(error)) from None

    current = conn.execute("SELECT * FROM policies WHERE user_id = %s", (user_id,)).fetchone()
    limits = DEFAULT_POLICIES[level] if current is None else lowered_policy(current, level)

    conn.execute(
        "INSERT INTO investor_profiles (user_id, risk_level, answers) VALUES (%s, %s, %s)"
        " ON CONFLICT (user_id) DO UPDATE"
        " SET risk_level = EXCLUDED.risk_level, answers = EXCLUDED.answers, updated_at = now()",
        (user_id, level, Jsonb(body.answers)),
    )
    conn.execute(
        "INSERT INTO policies (user_id, max_order_krw, max_daily_krw, max_weight_pct)"
        " VALUES (%(user_id)s, %(max_order_krw)s, %(max_daily_krw)s, %(max_weight_pct)s)"
        " ON CONFLICT (user_id) DO UPDATE SET max_order_krw = EXCLUDED.max_order_krw,"
        " max_daily_krw = EXCLUDED.max_daily_krw, max_weight_pct = EXCLUDED.max_weight_pct, updated_at = now()",
        {"user_id": user_id, **limits},
    )
    audit(conn, user_id, "profile_updated", {"risk_level": level, "policy": limits})
    conn.commit()
    return {
        "risk_level": level,
        "label": LABELS[level],
        "default_policy": as_json_numbers(DEFAULT_POLICIES[level]),
        "policy": policy_response(load_policy(conn, user_id)),
    }


@router.get("/policy")
def get_policy(conn: Conn, user_id: UserId) -> dict:
    return policy_response(load_policy(conn, user_id))


@router.put("/policy")
def put_policy(body: PolicyRequest, conn: Conn, user_id: UserId) -> dict:
    """한도 수정. 성향 기본값보다 높아도 저장하고 warnings로 알려준다 (FR-07a)."""
    before = load_policy(conn, user_id)
    conn.execute(
        "UPDATE policies SET max_order_krw = %(max_order_krw)s, max_daily_krw = %(max_daily_krw)s,"
        " max_weight_pct = %(max_weight_pct)s, fee_rate_pct = %(fee_rate_pct)s, updated_at = now()"
        " WHERE user_id = %(user_id)s",
        {"user_id": user_id, **body.model_dump()},
    )
    audit(conn, user_id, "policy_updated", {
        "before": {key: before[key] for key in (*LIMIT_FIELDS, "fee_rate_pct")},
        "after": body.model_dump(),
    })
    conn.commit()
    return policy_response(load_policy(conn, user_id))
