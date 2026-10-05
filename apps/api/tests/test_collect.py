"""수집 명령 테스트. 공공데이터포털·OpenDART·임베딩은 가짜로 바꿔 끼운다."""

from datetime import date

import psycopg
import pytest
from psycopg.rows import dict_row

from app import collect
from app.integrations import market_data, opendart


def price_row(code, name, day, close, cap):
    return {"stock_code": code, "stock_name": name, "trade_date": day, "close": close,
            "market_cap": cap, "listed_shares": cap // close}


@pytest.fixture
def conn(migrated):
    with psycopg.connect(migrated, row_factory=dict_row) as c:
        yield c
        c.rollback()


def test_amount_parsing() -> None:
    assert collect.amount("1,234") == 1234
    assert collect.amount("-1,234") == -1234
    assert collect.amount("-") is None
    assert collect.amount("") is None
    assert collect.amount(None) is None


def test_collect_prices_marks_top_by_market_cap_on_latest_day(conn, monkeypatch) -> None:
    old, new = date(2026, 10, 1), date(2026, 10, 2)
    rows = [
        price_row("111111", "작은회사", new, 1000, 10_000),
        price_row("222222", "큰회사", new, 5000, 900_000),
        price_row("333333", "어제만큰회사", old, 9000, 9_000_000),  # 최신일이 아니라 순위에서 빠진다
    ]

    def fake_daily_prices(api_key, begin, end, stock_code=None):
        return [r for r in rows if stock_code in (None, r["stock_code"])]

    monkeypatch.setattr(market_data, "daily_prices", fake_daily_prices)
    monkeypatch.setattr(collect, "TARGET_COUNT", 1)

    assert collect.collect_prices(conn, "key", new) == ["222222"]
    targets = conn.execute("SELECT code FROM stocks WHERE is_target").fetchall()
    assert [t["code"] for t in targets] == ["222222"]
    assert conn.execute("SELECT close FROM stock_prices WHERE stock_code = '222222'").fetchone()["close"] == 5000


def test_collect_financials_and_disclosures(conn, monkeypatch) -> None:
    conn.execute("INSERT INTO stocks (code, name, market) VALUES ('999999', '테스트회사', 'KOSPI') ON CONFLICT DO NOTHING")
    accounts = [
        {"fs_div": "CFS", "account_nm": "자본총계", "thstrm_amount": "1,000", "frmtrm_amount": "900", "rcept_no": "R1"},
        {"fs_div": "CFS", "account_nm": "당기순이익(손실)", "thstrm_amount": "-50", "frmtrm_amount": "-", "rcept_no": "R1"},
    ]
    monkeypatch.setattr(opendart, "major_accounts",
                        lambda corp, year, reprt, key: accounts if (year, reprt) == (2025, "11011") else [])
    filing = {"rcept_no": "R1", "report_nm": "사업보고서 (2025.12) ", "rcept_dt": "20260310"}
    other = {"rcept_no": "R2", "report_nm": "주요사항보고서", "rcept_dt": "20260401"}
    monkeypatch.setattr(opendart, "disclosures",
                        lambda corp, key, begin, end, kind=None: [filing] if kind == "A" else [other, filing])
    monkeypatch.setattr(opendart, "document_sections",
                        lambda rcept_no, key, wanted: [("II. 사업의 내용", "반도체를 만든다. " * 200)])
    embedded = []
    monkeypatch.setattr(collect.llm, "embed_documents",
                        lambda texts: embedded.extend(texts) or [[0.1] * 768 for _ in texts])

    assert collect.collect_financials(conn, "key", "999999", "C1", 2026) == 2
    first = collect.collect_disclosures(conn, "key", "999999", "C1", date(2026, 10, 5))
    second = collect.collect_disclosures(conn, "key", "999999", "C1", date(2026, 10, 5))

    row = conn.execute("SELECT amount, prev_amount FROM financials WHERE stock_code = '999999'"
                       " AND account = '당기순이익(손실)'").fetchone()
    assert (row["amount"], row["prev_amount"]) == (-50, None)
    assert conn.execute("SELECT count(*) AS n FROM disclosures WHERE stock_code = '999999'").fetchone()["n"] == 2
    chunks = conn.execute("SELECT count(*) AS n, min(section) AS section FROM disclosure_chunks WHERE rcept_no = 'R1'").fetchone()
    assert chunks["n"] == len(embedded) > 1
    assert chunks["section"] == "II. 사업의 내용"
    assert "본문" in first and "이미 조각냄" in second  # 두 번째 실행은 다시 임베딩하지 않는다


def test_sections_of_extracts_titles_and_plain_text() -> None:
    document = ("<SECTION-1><TITLE>I. 회사의 개요</TITLE><P>개요</P></SECTION-1>"
                "<SECTION-1><TITLE ATOC=\"Y\">II. 사업의 내용</TITLE><P>메모리 &amp; 파운드리</P>"
                "<TABLE><TR><TD>매출</TD></TR></TABLE></SECTION-1>")
    assert opendart.sections_of(document) == [
        ("I. 회사의 개요", "I. 회사의 개요 개요"),
        ("II. 사업의 내용", "II. 사업의 내용 메모리 & 파운드리 매출"),
    ]
