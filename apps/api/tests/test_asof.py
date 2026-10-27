"""날짜로 자른 보기에 그날 이후 자료가 새지 않는지 (DB가 켜져 있어야 한다)"""
import os

import pytest
from psycopg import connect

from app.asof import asof_url

URL = os.environ.get("DATABASE_URL", "")
DAY = "2026-03-05"


@pytest.fixture
def conn():
    if not URL:
        pytest.skip("DATABASE_URL 없음")
    with connect(asof_url(URL, DAY)) as c:
        try:
            c.execute("SELECT 1 FROM simasof.price LIMIT 1")
        except Exception:
            pytest.skip("python -m app.asof setup 을 먼저")
        yield c


def test_nothing_from_that_day_or_later(conn):
    assert str(conn.execute("SELECT max(trade_date) FROM stock_prices").fetchone()[0]) < DAY
    assert str(conn.execute("SELECT max(filed_at) FROM disclosures").fetchone()[0]) < DAY
    assert conn.execute("SELECT max(left(rcept_no, 8)) FROM financials").fetchone()[0] < DAY.replace("-", "")
    assert conn.execute("SELECT count(*) FROM disclosure_chunks c JOIN public.disclosures d USING (rcept_no) WHERE d.filed_at >= %s", (DAY,)).fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM news WHERE published_at >= now()").fetchone()[0] == 0


def test_now_is_that_morning(conn):
    assert str(conn.execute("SELECT (now() AT TIME ZONE 'Asia/Seoul')::text").fetchone()[0]).startswith(f"{DAY} 09:00")
