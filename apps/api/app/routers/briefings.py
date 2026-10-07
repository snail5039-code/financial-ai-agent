"""아침 브리핑 보기 (app/briefing.py가 만든 것). 그 사용자 것만 보여준다."""

from fastapi import APIRouter, HTTPException

from app.db import Conn
from app.routers.auth import UserId

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


@router.get("/latest")
def latest(conn: Conn, user_id: UserId) -> dict:
    row = conn.execute(
        "SELECT id, brief_date, content, created_at FROM briefings WHERE user_id = %s ORDER BY brief_date DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "아직 아침 브리핑이 없어요")
    return row
