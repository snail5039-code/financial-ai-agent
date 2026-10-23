"""에뮬레이터 앱 자산 화면 캡처 (임시). apps/api에서:
    uv run python capture.py <이유>          한 번 캡처 (예: hourly, close)
    uv run python capture.py --watch         새 주문이 생길 때마다 캡처 (장중 15:35까지)
docs/reports/img/live-YYYYMMDD/HHMM_<이유>_top.png, _holdings.png 로 저장한다 (10/16 캡처와 같은 이름 규칙)."""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ADB = r"C:\Users\snail\dev\android\platform-tools\adb.exe"
REPO = Path(r"C:\puh\multicam\financial-ai-agent")
KST = ZoneInfo("Asia/Seoul")


def adb(*args, out=None):
    return subprocess.run([ADB, *args], stdout=out, check=False, timeout=30)


def shot(path):
    with open(path, "wb") as f:
        adb("exec-out", "screencap", "-p", out=f)


def capture(reason):
    now = datetime.now(KST)
    folder = REPO / "docs" / "reports" / "img" / f"live-{now:%Y%m%d}"
    folder.mkdir(parents=True, exist_ok=True)
    for x in ("108", "324"):  # 채팅 탭 → 자산 탭 (다른 탭에서 옮겨 와야 잔고를 다시 받는다, 모의 잔고 조회 ~12초)
        adb("shell", "input", "tap", x, "2232")
        time.sleep(2)
    time.sleep(16)  # 잔고 뒤에 그래프(/api/equity)도 받게
    for _ in range(3):  # 맨 위로 (탭을 옮겨도 스크롤 위치가 남는다)
        adb("shell", "input", "swipe", "540", "500", "540", "2000", "200")
    time.sleep(1)
    stem = folder / f"{now:%H%M}_{reason}"
    shot(f"{stem}_top.png")
    adb("shell", "input", "swipe", "540", "1600", "540", "400", "400")  # 보유 종목으로
    time.sleep(1.5)
    shot(f"{stem}_holdings.png")
    adb("shell", "input", "swipe", "540", "400", "540", "1600", "400")  # 위로 되돌림
    print("캡처:", stem.name, flush=True)


def watch():
    from dotenv import load_dotenv
    load_dotenv(".env")
    import psycopg
    url = os.environ["DATABASE_URL"].replace(":5432/", ":5433/")
    sql = ("SELECT o.id, o.side, p.stock_code FROM orders o JOIN approvals a ON a.id = o.approval_id"
           " JOIN proposals p ON p.id = a.proposal_id WHERE o.created_at > now() - interval '1 day'")
    with psycopg.connect(url) as c:
        seen = {r[0] for r in c.execute(sql)}
    while datetime.now(KST).strftime("%H%M") < "1535":
        time.sleep(30)
        with psycopg.connect(url) as c:
            new = [r for r in c.execute(sql) if r[0] not in seen]
        if new:
            seen |= {r[0] for r in new}
            time.sleep(10)  # 체결·잔고 반영을 조금 기다린다
            capture("_".join(sorted({f"{side}_{code}" for _, side, code in new}))[:60])


if __name__ == "__main__":
    watch() if sys.argv[1:] == ["--watch"] else capture(sys.argv[1] if len(sys.argv) > 1 else "manual")
