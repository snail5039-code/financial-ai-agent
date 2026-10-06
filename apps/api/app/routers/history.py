"""기록: 분석·주문 목록과 한 건의 전체 과정 (FR-35, FR-36, 화면 S-10·S-11).

한 건 = 제안서 하나. 제안 → 검증(반박-수정 회차마다) → 정책 검사 → 승인 → 주문 결과를 시간순으로 보여준다.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db import Conn
from app.routers.auth import UserId

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
def list_history(conn: Conn, user_id: UserId) -> list[dict]:
    return conn.execute(
        """
        SELECT p.id AS proposal_id, p.created_at, p.stock_code, s.name AS stock_name, p.action, p.qty, p.limit_price,
               p.user_directed,
               (SELECT verdict FROM verifications v WHERE v.proposal_id = p.id ORDER BY round DESC LIMIT 1) AS verdict,
               (SELECT ok FROM policy_checks pc WHERE pc.proposal_id = p.id) AS policy_ok,
               CASE WHEN a.status = 'pending' AND a.expires_at <= now() THEN 'expired' ELSE a.status END AS approval_status,
               (SELECT status FROM orders o WHERE o.approval_id = a.id ORDER BY created_at LIMIT 1) AS order_status
        FROM proposals p
        JOIN stocks s ON s.code = p.stock_code
        LEFT JOIN approvals a ON a.proposal_id = p.id
        WHERE p.user_id = %s
        ORDER BY p.created_at DESC LIMIT 100
        """,
        (user_id,),
    ).fetchall()


@router.get("/history/{proposal_id}")
def get_history(proposal_id: UUID, conn: Conn, user_id: UserId) -> dict:
    proposal = conn.execute(
        "SELECT p.*, s.name AS stock_name FROM proposals p JOIN stocks s ON s.code = p.stock_code"
        " WHERE p.id = %s AND p.user_id = %s", (proposal_id, user_id),
    ).fetchone()
    if proposal is None:
        raise HTTPException(404, "기록을 찾을 수 없어요")

    timeline = [{"at": proposal["created_at"], "step": "proposal", "data": proposal}]
    for v in conn.execute("SELECT * FROM verifications WHERE proposal_id = %s ORDER BY round", (proposal_id,)):
        timeline.append({"at": v["created_at"], "step": "verification", "data": v})
    for check in conn.execute("SELECT * FROM policy_checks WHERE proposal_id = %s", (proposal_id,)):
        timeline.append({"at": check["created_at"], "step": "policy_check", "data": check})
    for approval in conn.execute("SELECT * FROM approvals WHERE proposal_id = %s", (proposal_id,)):
        timeline.append({"at": approval["created_at"], "step": "approval_requested", "data": approval})
        if approval["decided_at"]:
            timeline.append({"at": approval["decided_at"], "step": f"approval_{approval['status']}",
                             "data": {"channel": approval["decided_channel"]}})
        for order in conn.execute("SELECT * FROM orders WHERE approval_id = %s ORDER BY created_at", (approval["id"],)):
            timeline.append({"at": order["created_at"], "step": "order_result", "data": order})
    timeline.sort(key=lambda item: item["at"])
    return {"proposal_id": proposal_id, "stock_name": proposal["stock_name"], "timeline": timeline}
