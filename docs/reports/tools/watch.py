"""장중 점검 (임시). apps/api에서: uv run python <이 파일> [최근 몇 분, 기본 60]
오늘 분석·판단·주문, 최근 판단 근거, 서버·앱 로그 오류를 한 번에 본다."""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")
url = os.environ["DATABASE_URL"].replace(":5432/", ":5433/")
import psycopg  # noqa: E402
from psycopg.rows import dict_row  # noqa: E402

MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 60
SCRATCH = Path(__file__).parent
# 서버·앱 로그 위치. 기본은 임시 폴더의 api.log·flutter.log (10/30부터 이렇게 띄움). 다르면 환경변수 WATCH_API_LOG·WATCH_APP_LOG
LOGS = {"api.log": Path(os.environ.get("WATCH_API_LOG", Path(tempfile.gettempdir()) / "api.log")),
        "flutter.log": Path(os.environ.get("WATCH_APP_LOG", Path(tempfile.gettempdir()) / "flutter.log"))}
TODAY = "(x.created_at AT TIME ZONE 'Asia/Seoul')::date = (now() AT TIME ZONE 'Asia/Seoul')::date"


def short(v, n=110):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


with psycopg.connect(url, row_factory=dict_row) as c:
    q = lambda sql, *a: c.execute(sql, a).fetchall()
    src = open(r"C:\puh\multicam\financial-ai-agent\apps\api\app\agents\analysis.py", encoding="utf-8").read()
    limit = int(re.search(r"^MAX_ANALYSES_PER_DAY = (\d+)", src, re.M).group(1))
    reserve = int(re.search(r"^HOLDING_RESERVE = (\d+)", src, re.M).group(1))
    print(f"== 오늘 분석 (한도 {limit}, 안 가진 종목 {limit - reserve}) ==")
    rows = q(f"SELECT action, count(*) n FROM proposals x WHERE {TODAY} GROUP BY 1 ORDER BY 2 DESC")
    print("  합계", sum(r["n"] for r in rows), {r["action"]: r["n"] for r in rows})
    rows = q(f"SELECT v.verdict, count(*) n FROM verifications v JOIN proposals x ON x.id = v.proposal_id WHERE {TODAY} GROUP BY 1")
    print("  검증", {r["verdict"]: r["n"] for r in rows})
    rows = q(f"SELECT text, count(*) n FROM messages x WHERE role = 'assistant' AND {TODAY}"
             " AND text NOT LIKE '%%검증: 승인%%' AND (text LIKE '%%번까지 할 수 있어요%%' OR text LIKE '%%실패했어요%%' OR text LIKE '%%오류%%') GROUP BY 1")
    for r in rows:
        print(f"  거절·실패 {r['n']}번: {short(r['text'], 80)}")

    print("== 오늘 주문 ==")
    for r in q(f"SELECT to_char(x.created_at AT TIME ZONE 'Asia/Seoul','HH24:MI') t, s.name, x.side, x.kind, x.qty, x.price,"
               f" x.status, x.filled_qty, x.filled_price, x.message FROM orders x JOIN approvals a ON a.id = x.approval_id"
               f" JOIN proposals p ON p.id = a.proposal_id JOIN stocks s ON s.code = p.stock_code WHERE {TODAY} ORDER BY x.created_at"):
        print(f"  {r['t']} {r['name']} {r['side']}/{r['kind']} {r['qty']}주 @{r['price']:,} {r['status']}"
              f" 체결 {r['filled_qty']}주 @{r['filled_price'] or '-'} {short(r['message'] or '', 60)}")

    print(f"== 최근 {MIN}분 판단 ==")
    for r in q(f"SELECT to_char(x.created_at AT TIME ZONE 'Asia/Seoul','HH24:MI') t, s.name, x.action, x.qty, x.limit_price,"
               f" x.claims, x.counter_arguments, (SELECT verdict || ' ' || summary FROM verifications v WHERE v.proposal_id = x.id"
               f" ORDER BY round DESC LIMIT 1) ver FROM proposals x JOIN stocks s ON s.code = x.stock_code"
               f" WHERE x.created_at > now() - make_interval(mins => %s) ORDER BY x.created_at", MIN):
        claims = [cl.get("text") if isinstance(cl, dict) else cl for cl in r["claims"]][:2]
        print(f"  {r['t']} {r['name']} {r['action']} {r['qty'] or ''}주 @{r['limit_price'] or ''}")
        for cl in claims:
            print(f"      근거: {short(cl)}")
        print(f"      검증: {short(r['ver'] or '없음')}")

    snap = c.execute("SELECT cash_krw, holdings, fetched_at AT TIME ZONE 'Asia/Seoul' t FROM account_snapshots"
                     " ORDER BY fetched_at DESC LIMIT 1").fetchone()
    if snap:
        print(f"== 마지막 잔고 ({snap['t']:%H:%M}) 현금 {snap['cash_krw']:,} ==")
        for h in snap["holdings"]:
            print("  " + short({k: h.get(k) for k in ("stock_name", "qty", "avg_price", "price", "pnl_pct", "profit_rate") if k in h}, 140))

for name, bad, skip in (("api.log", r"Traceback|ERROR|Exception| 5\d\d ", r"RemoteException"),
                        ("flutter.log", r"Exception|Error|error:|오류|실패", r"Firebase|Kotlin|FirebaseOptions|values\.xml")):
    path = LOGS.get(name, SCRATCH / name)  # 서버는 로그인 자동 시작 로그 (PowerShell이 UTF-16으로 섞어 써서 \0을 뺀다)
    lines = path.read_text(encoding="utf-8", errors="replace").replace("\0", "").splitlines() if path.exists() else []
    hits = [l for l in lines if re.search(bad, l) and not (skip and re.search(skip, l))]
    print(f"== {name}: 문제 줄 {len(hits)}개 (전체 {len(lines)}줄) ==")
    for l in hits[-6:]:
        print("  " + short(l, 160))
