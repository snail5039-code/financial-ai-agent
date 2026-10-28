"""날짜로 자른 시험용 보기 (2단계 AI 판단 시험용 개발 도구, 서버 실행에는 안 쓴다).

앱의 분석 코드는 "지금" 기준으로 DB를 읽는다. 읽는 표 이름과 now()를 같은 이름의 보기·함수로 바꿔 끼우면 코드를 안 고치고 과거 어느 날 아침의 시점으로 돌릴 수 있다.
    uv run python -m app.asof setup          # 시험용 표·보기 만들기 (일봉은 tools/data/kis/daily에서 읽는다)
    uv run python -m app.asof news           # 시험 구간의 과거 뉴스 제목 받기 (무료, 구글 뉴스)
쓸 때는 asof_url(DATABASE_URL, "2026-03-05")로 접속 주소를 만들어 분석에 넘긴다. 실제 표는 건드리지 않는다.
"""

import json
import sys
from pathlib import Path
from urllib.parse import quote

from psycopg import connect

DAILY = Path(__file__).resolve().parents[3] / "tools" / "data" / "kis" / "daily"
# 그날 09:00(한국) 시점으로 본다. 그 전에 나온 것만 보인다. 시세는 하루 늦게 오니 어제 종가까지, 공시·뉴스는 그날 새벽까지
DAY = "current_setting('simasof.day')::date"
SETUP = f"""
CREATE SCHEMA IF NOT EXISTS simasof;
CREATE TABLE IF NOT EXISTS simasof.price (stock_code text, trade_date date, close bigint, market_cap bigint, listed_shares bigint, PRIMARY KEY (stock_code, trade_date));
CREATE OR REPLACE FUNCTION simasof.now() RETURNS timestamptz LANGUAGE sql STABLE AS $$ SELECT ({DAY} + time '09:00') AT TIME ZONE 'Asia/Seoul' $$;
CREATE OR REPLACE VIEW simasof.stock_prices AS SELECT * FROM simasof.price WHERE trade_date < {DAY};
CREATE OR REPLACE VIEW simasof.disclosures AS SELECT * FROM public.disclosures WHERE filed_at < {DAY};
CREATE OR REPLACE VIEW simasof.disclosure_chunks AS SELECT c.* FROM public.disclosure_chunks c JOIN simasof.disclosures d USING (rcept_no);
CREATE OR REPLACE VIEW simasof.financials AS SELECT * FROM public.financials WHERE left(rcept_no, 8)::date < {DAY};
CREATE TABLE IF NOT EXISTS simasof.news_old (LIKE public.news INCLUDING DEFAULTS, UNIQUE (stock_code, url));
CREATE OR REPLACE VIEW simasof.news AS SELECT * FROM (SELECT * FROM public.news UNION SELECT * FROM simasof.news_old) n WHERE published_at < simasof.now();
"""


# 시험 구간 (지수만 보고 미리 정함, 2026-10-27): 20거래일씩. 뉴스는 구간 시작 7일 전부터 받는다
WINDOWS = {"up": ("2026-05-04", "2026-06-02"), "crash": ("2026-07-01", "2026-07-29"), "flat": ("2025-11-27", "2025-12-24"),
           # 규칙 따르기 프롬프트 시험용 새 구간 (지수만 보고 고름: 보통 오름 +17.7%, 보통 내림 -15.8%)
           "up2": ("2026-01-19", "2026-02-19"), "down2": ("2026-09-14", "2026-10-16")}


def asof_url(base: str, day: str) -> str:
    """분석 코드가 쓸 접속 주소. 시험용 보기가 실제 표보다, simasof.now()가 now()보다 먼저 잡힌다"""
    options = quote(f"-c search_path=simasof,pg_catalog,public -c simasof.day={day} -c TimeZone=Asia/Seoul", safe="")
    return f"{base}{'&' if '?' in base else '?'}options={options}"


def setup(url: str) -> int:
    """시험용 보기를 만들고 일봉을 채운다. 시총은 일봉에 없어 종가 × 상장주식수(실제 표의 가장 최근 값)로 어림한다 (과거 증자·분할은 반영 안 됨)"""
    with connect(url) as conn:
        conn.execute(SETUP)
        shares = dict(conn.execute("SELECT DISTINCT ON (stock_code) stock_code, listed_shares FROM public.stock_prices ORDER BY stock_code, trade_date DESC").fetchall())
        rows = [(f.stem, f"{b['d'][:4]}-{b['d'][4:6]}-{b['d'][6:]}", b["c"], b["c"] * shares[f.stem], shares[f.stem])
                for f in sorted(DAILY.glob("*.json")) if f.stem in shares for b in json.loads(f.read_text(encoding="utf-8"))]
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO simasof.price VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING", rows)
    return len(rows)


def fetch_news(url: str, gap: float = 1.5) -> int:
    """구간별 과거 뉴스 제목을 구글 뉴스 RSS(after:/before:)에서 받아 simasof.news_old에 넣는다 (제목·언론사·시각·링크만). 이미 받은 종목·구간은 건너뛴다"""
    import time
    from datetime import date, timedelta

    import httpx

    from app.integrations.google_news import URL as RSS, parse

    saved = 0
    with connect(url) as conn, httpx.Client(timeout=15, follow_redirects=True) as client:
        stocks = conn.execute("SELECT code, name FROM public.stocks").fetchall()
        for key, (start, end) in WINDOWS.items():
            begin, stop = date.fromisoformat(start) - timedelta(days=7), date.fromisoformat(end) + timedelta(days=1)
            for code, name in stocks:
                if conn.execute("SELECT 1 FROM simasof.news_old WHERE stock_code = %s AND published_at >= %s AND published_at < %s AND fetched_at < '2000-01-02'", (code, begin, stop)).fetchone():
                    continue  # 받은 표시: fetched_at을 2000-01-01로 남긴다
                longer = tuple(n for _, n in stocks if name in n and n != name)
                for attempt in range(3):
                    try:
                        r = client.get(RSS, params={"q": f'"{name}" after:{begin} before:{stop}', "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
                        r.raise_for_status()
                        break
                    except httpx.HTTPError:
                        time.sleep(5 * (attempt + 1))
                else:
                    print("실패", key, name, flush=True)
                    continue
                time.sleep(gap)
                for item in parse(r.text, name, longer):
                    saved += conn.execute("INSERT INTO simasof.news_old (stock_code, title, press, url, published_at, fetched_at) VALUES (%s,%s,%s,%s,%s,'2000-01-01') ON CONFLICT DO NOTHING",
                                          (code, item["title"], item["press"], item["url"], item["published_at"])).rowcount
                conn.commit()
            print("뉴스", key, "누적", saved, flush=True)
    return saved


if __name__ == "__main__":
    import os
    if sys.argv[1:] == ["setup"]:
        print("일봉", setup(os.environ["DATABASE_URL"]), "줄")
    elif sys.argv[1:] == ["news"]:
        print("뉴스", fetch_news(os.environ["DATABASE_URL"]), "건")
    else:
        sys.exit(__doc__)
