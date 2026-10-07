"""관심 종목 (docs/plan/12-todo-by-stage.md 2-3). 채팅 탭 동그라미, 아침 브리핑(소식·매수 후보)에 쓴다."""

from fastapi import APIRouter, HTTPException

from app.db import Conn
from app.routers.auth import UserId

router = APIRouter(prefix="/api", tags=["watchlist"])
MAX_WATCH = 30


@router.get("/stocks")
def list_stocks(conn: Conn, user_id: UserId) -> list[dict]:
    """관심 종목을 고를 수 있는 종목 (지금은 분석 대상만). watching: 내 관심 종목인지."""
    return conn.execute(
        "SELECT s.code, s.name, EXISTS (SELECT 1 FROM watchlist w WHERE w.user_id = %s AND w.stock_code = s.code) AS watching"
        " FROM stocks s WHERE s.is_target ORDER BY s.name",
        (user_id,),
    ).fetchall()


@router.get("/watchlist")
def list_watchlist(conn: Conn, user_id: UserId) -> list[dict]:
    return conn.execute(
        "SELECT w.stock_code, s.name AS stock_name, w.created_at FROM watchlist w JOIN stocks s ON s.code = w.stock_code"
        " WHERE w.user_id = %s ORDER BY w.created_at",
        (user_id,),
    ).fetchall()


@router.put("/watchlist/{stock_code}", status_code=204)
def add_watch(stock_code: str, conn: Conn, user_id: UserId) -> None:
    if not conn.execute("SELECT 1 FROM stocks WHERE code = %s AND is_target", (stock_code,)).fetchone():
        raise HTTPException(404, "관심 종목으로 넣을 수 없는 종목이에요 (지금은 분석 대상만)")
    count = conn.execute("SELECT count(*) AS n FROM watchlist WHERE user_id = %s", (user_id,)).fetchone()["n"]
    if count >= MAX_WATCH:
        raise HTTPException(422, f"관심 종목은 {MAX_WATCH}개까지예요")
    conn.execute("INSERT INTO watchlist (user_id, stock_code) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, stock_code))
    conn.commit()


@router.delete("/watchlist/{stock_code}", status_code=204)
def remove_watch(stock_code: str, conn: Conn, user_id: UserId) -> None:
    conn.execute("DELETE FROM watchlist WHERE user_id = %s AND stock_code = %s", (user_id, stock_code))
    conn.commit()
