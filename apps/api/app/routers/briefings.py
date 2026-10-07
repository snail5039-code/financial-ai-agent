"""아침 브리핑 보기 (app/briefing.py가 만든 것). 그 사용자 것만 보여준다."""

from typing import Literal

from fastapi import APIRouter, HTTPException

from app.db import Conn
from app.routers.auth import UserId

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


@router.get("/latest")
def latest(conn: Conn, user_id: UserId, kind: Literal["morning", "close"] = "morning") -> dict:
    """가장 최근 아침 브리핑(morning) 또는 장 마감 요약(close)."""
    row = conn.execute(
        "SELECT id, brief_date, kind, content, created_at FROM briefings WHERE user_id = %s AND kind = %s"
        " ORDER BY brief_date DESC LIMIT 1",
        (user_id, kind),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "아직 아침 브리핑이 없어요" if kind == "morning" else "아직 장 마감 요약이 없어요")
    return row
