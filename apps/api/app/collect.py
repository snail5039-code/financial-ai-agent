"""분석에 쓰는 데이터 모으기. 실행: uv run python -m app.collect

1. 시세 (공공데이터포털): 코스피 시가총액 상위 30개를 분석 대상(stocks.is_target)으로 정하고 최근 100일 종가를 받는다
2. 재무 (OpenDART): 대상 종목의 올해·작년 정기보고서 주요 계정
3. 공시 (OpenDART): 최근 1년 공시 목록, 최신 정기보고서의 "사업의 내용"·"경영진단" 본문 → 조각 → 임베딩

여러 번 실행해도 된다. 받은 값은 덮어쓰고, 이미 조각낸 공시는 건너뛴다.
    --skip-prices   1단계를 건너뛰고 지금 분석 대상 종목으로만 (시세 키가 아직 안 될 때)
    --codes A,B     이 종목들만 (stocks에 이미 있어야 함)
"""

import argparse
from datetime import datetime, timedelta

import psycopg
from psycopg.rows import dict_row

from app import config
from app.agents import llm
from app.clock import KST
from app.db import connect
from app.functions.text import split_text
from app.integrations import market_data, opendart

TARGET_COUNT = 30
PRICE_DAYS = 100
DISCLOSURE_DAYS = 365
WANTED_SECTIONS = ("사업의 내용", "경영진단")
EMBED_BATCH = 100


def amount(text: str | None) -> int | None:
    """OpenDART 금액 문자열 ("1,234", "-1,234", "-", "") → 정수."""
    cleaned = (text or "").replace(",", "").strip()
    return int(cleaned) if cleaned not in ("", "-") else None


# ---------- 1. 시세 ----------

def collect_prices(conn: psycopg.Connection, api_key: str, today) -> list[str]:
    recent = market_data.daily_prices(api_key, today - timedelta(days=10), today)
    latest = max(row["trade_date"] for row in recent)
    top = sorted((r for r in recent if r["trade_date"] == latest), key=lambda r: r["market_cap"], reverse=True)
    top = top[:TARGET_COUNT]
    print(f"[시세] {latest} 기준 시가총액 상위 {len(top)}개")

    conn.execute("UPDATE stocks SET is_target = false")
    for row in top:
        conn.execute(
            "INSERT INTO stocks (code, name, market, is_target) VALUES (%s, %s, 'KOSPI', true)"
            " ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, is_target = true",
            (row["stock_code"], row["stock_name"]),
        )
    for row in top:
        history = market_data.daily_prices(api_key, today - timedelta(days=PRICE_DAYS), today, row["stock_code"])
        for day in history:
            conn.execute(
                "INSERT INTO stock_prices (stock_code, trade_date, close, market_cap, listed_shares)"
                " VALUES (%(stock_code)s, %(trade_date)s, %(close)s, %(market_cap)s, %(listed_shares)s)"
                " ON CONFLICT (stock_code, trade_date) DO UPDATE SET close = EXCLUDED.close,"
                " market_cap = EXCLUDED.market_cap, listed_shares = EXCLUDED.listed_shares",
                day,
            )
        print(f"  {row['stock_name']}({row['stock_code']}) 종가 {len(history)}일")
    conn.commit()
    return [row["stock_code"] for row in top]


# ---------- 2. 재무 ----------

def collect_financials(conn: psycopg.Connection, api_key: str, code: str, corp_code: str, year: int) -> int:
    count = 0
    for bsns_year in (year - 1, year):
        for reprt_code in opendart.REPORT_CODES:
            for row in opendart.major_accounts(corp_code, bsns_year, reprt_code, api_key):
                conn.execute(
                    "INSERT INTO financials (stock_code, bsns_year, reprt_code, fs_div, account, amount, prev_amount, rcept_no)"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    " ON CONFLICT (stock_code, bsns_year, reprt_code, fs_div, account) DO UPDATE"
                    " SET amount = EXCLUDED.amount, prev_amount = EXCLUDED.prev_amount, rcept_no = EXCLUDED.rcept_no",
                    (code, bsns_year, reprt_code, row["fs_div"], row["account_nm"],
                     amount(row.get("thstrm_amount")), amount(row.get("frmtrm_amount")), row["rcept_no"]),
                )
                count += 1
    return count


# ---------- 3. 공시 ----------

def save_disclosure(conn: psycopg.Connection, code: str, item: dict) -> None:
    conn.execute(
        "INSERT INTO disclosures (rcept_no, stock_code, title, url, filed_at) VALUES (%s, %s, %s, %s, %s)"
        " ON CONFLICT (rcept_no) DO NOTHING",
        (item["rcept_no"], code, item["report_nm"].strip(), opendart.disclosure_url(item["rcept_no"]),
         datetime.strptime(item["rcept_dt"], "%Y%m%d").date()),
    )


def collect_disclosures(conn: psycopg.Connection, api_key: str, code: str, corp_code: str, today) -> str:
    begin, end = f"{today - timedelta(days=DISCLOSURE_DAYS):%Y%m%d}", f"{today:%Y%m%d}"
    items = opendart.disclosures(corp_code, api_key, begin, end)
    for item in items:
        save_disclosure(conn, code, item)

    periodic = opendart.disclosures(corp_code, api_key, begin, end, kind="A")
    if not periodic:
        return f"공시 {len(items)}건, 정기보고서 없음"
    report = periodic[0]  # 최신 정기보고서
    save_disclosure(conn, code, report)
    if conn.execute("SELECT 1 FROM disclosure_chunks WHERE rcept_no = %s LIMIT 1", (report["rcept_no"],)).fetchone():
        return f"공시 {len(items)}건, {report['report_nm'].strip()} 이미 조각냄"

    chunks = [
        (title, chunk)
        for title, text in opendart.document_sections(report["rcept_no"], api_key, WANTED_SECTIONS)
        for chunk in split_text(text)
    ]
    for start in range(0, len(chunks), EMBED_BATCH):
        batch = chunks[start:start + EMBED_BATCH]
        vectors = llm.embed_documents([chunk for _, chunk in batch])
        for seq, ((title, chunk), vector) in enumerate(zip(batch, vectors), start=start):
            conn.execute(
                "INSERT INTO disclosure_chunks (rcept_no, seq, section, content, embedding)"
                " VALUES (%s, %s, %s, %s, %s::vector)",
                (report["rcept_no"], seq, title, chunk, str(vector)),
            )
    return f"공시 {len(items)}건, {report['report_nm'].strip()} 본문 {len(chunks)}조각"


# ---------- 실행 ----------

def main() -> None:
    parser = argparse.ArgumentParser(description="분석용 시세·재무·공시 수집")
    parser.add_argument("--skip-prices", action="store_true")
    parser.add_argument("--codes", help="쉼표로 구분한 종목 코드")
    args = parser.parse_args()
    if not config.OPENDART_API_KEY:
        raise SystemExit("OPENDART_API_KEY가 비어 있습니다 (apps/api/.env)")
    today = datetime.now(KST).date()

    with connect(config.DATABASE_URL, row_factory=dict_row) as conn:
        if args.codes:
            codes = args.codes.split(",")
        elif args.skip_prices:
            codes = [row["code"] for row in conn.execute("SELECT code FROM stocks WHERE is_target")]
        else:
            if not config.DATA_GO_KR_API_KEY:
                raise SystemExit("DATA_GO_KR_API_KEY가 비어 있습니다 (apps/api/.env)")
            codes = collect_prices(conn, config.DATA_GO_KR_API_KEY, today)

        corp_of = opendart.corp_codes(config.OPENDART_API_KEY)
        for code in codes:
            name = conn.execute("SELECT name FROM stocks WHERE code = %s", (code,)).fetchone()
            if name is None or code not in corp_of:
                print(f"[건너뜀] {code}: stocks 또는 OpenDART 회사 목록에 없음")
                continue
            financial_rows = collect_financials(conn, config.OPENDART_API_KEY, code, corp_of[code], today.year)
            summary = collect_disclosures(conn, config.OPENDART_API_KEY, code, corp_of[code], today)
            conn.commit()
            print(f"[재무·공시] {name['name']}({code}) 재무 {financial_rows}줄, {summary}")


if __name__ == "__main__":
    main()
