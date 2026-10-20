"""계좌 스냅샷: 폰이 증권사에서 조회한 계좌 요약을 올리고, 웹이 그것으로 잔고를 보여준다 (docs/plan/02-architecture.md 5장).

계좌번호는 받지 않는다 (Balance는 정해진 칸 외에는 거부). 그 사용자에게만 보여준다 (NFR-05a).
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from app.agents.interrupts import Balance
from app.agents.query import latest_snapshot
from app.db import Conn
from app.routers.auth import UserId

router = APIRouter(prefix="/api", tags=["snapshot"])


@router.post("/snapshot", status_code=204)
def post_snapshot(body: Balance, conn: Conn, user_id: UserId) -> None:
    holdings = body.model_dump(mode="json")["holdings"]
    conn.execute(
        "INSERT INTO account_snapshots (user_id, cash_krw, holdings, fetched_at, total_krw) VALUES (%s, %s, %s, %s, %s)",
        (user_id, body.cash_krw, Jsonb(holdings), body.fetched_at, body.total_krw),
    )
    conn.commit()


class Deferral(BaseModel):
    """자동매매가 매도 판단을 미룬 것 (auto_trader.dart deferSell). 점수표가 종가와 비교한다"""
    stock_code: str = Field(pattern=r"^\d{6}$")
    reason: Literal["stop", "drop", "giveback", "market"]
    price: int = Field(gt=0, le=100_000_000)
    market_pct: float | None = Field(default=None, ge=-30, le=30)
    stock_pct: float | None = Field(default=None, ge=-30, le=30)


@router.post("/auto/deferrals", status_code=204)
def post_deferral(body: Deferral, conn: Conn, user_id: UserId) -> None:
    if not conn.execute("SELECT 1 FROM stocks WHERE code = %s", (body.stock_code,)).fetchone():
        raise HTTPException(404, "분석 대상 종목이 아니에요")
    conn.execute("INSERT INTO sell_deferrals (user_id, stock_code, reason, price, market_pct, stock_pct) VALUES (%s, %s, %s, %s, %s, %s)",
                 (user_id, body.stock_code, body.reason, body.price, body.market_pct, body.stock_pct))
    conn.commit()


@router.get("/equity")
def get_equity(conn: Conn, user_id: UserId) -> dict:
    """총자산 기록 (자산 탭 그래프): 날짜별은 그날 마지막 값, 장중은 기록이 있는 가장 최근 날의 값 전부. 폰이 계산해 올린 값만 쓴다."""
    rows = conn.execute(
        "SELECT (fetched_at AT TIME ZONE 'Asia/Seoul')::date AS day, to_char(fetched_at AT TIME ZONE 'Asia/Seoul', 'HH24:MI') AS time,"
        " total_krw FROM account_snapshots WHERE user_id = %s AND total_krw IS NOT NULL"
        " AND fetched_at >= now() - interval '120 days' ORDER BY fetched_at",
        (user_id,),
    ).fetchall()
    days = {str(r["day"]): r["total_krw"] for r in rows}  # 시간순이라 마지막 값이 남는다
    last = str(rows[-1]["day"]) if rows else None
    return {"days": [{"date": d, "total_krw": v} for d, v in days.items()],
            "intraday": {"date": last, "points": [{"time": r["time"], "total_krw": r["total_krw"]}
                                                  for r in rows if str(r["day"]) == last]}}


@router.get("/snapshot")
def get_snapshot(conn: Conn, user_id: UserId) -> dict:
    row = latest_snapshot(conn, user_id)
    if row is None:
        raise HTTPException(404, "아직 동기화된 계좌가 없어요. 폰 앱을 열어 주세요.")
    return row
