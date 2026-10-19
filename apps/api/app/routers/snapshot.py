"""계좌 스냅샷: 폰이 증권사에서 조회한 계좌 요약을 올리고, 웹이 그것으로 잔고를 보여준다 (docs/plan/02-architecture.md 5장).

계좌번호는 받지 않는다 (Balance는 정해진 칸 외에는 거부). 그 사용자에게만 보여준다 (NFR-05a).
"""

from fastapi import APIRouter, HTTPException
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
