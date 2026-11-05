"""과거 일별 거래량·거래대금 받기 (백테스트용 개발 도구, 읽기 전용). 앱·서버와 따로 돈다.

    python tools/kis_volume.py 005930 000660 ...   # 일별 {d 날짜, c 종가, v 거래량, a 거래대금} 1년치 → tools/data/kis/volume/<종목>.json

KIS 모의투자 서버의 시세 조회만 쓴다. 키는 apps/client/dev_s.env에서 읽고 출력하지 않는다. 이미 받은 것은 다시 받지 않는다. 장 마감 뒤에 돌린다.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kis_history import get  # noqa: E402
from kis_mock_check import load_keys, token  # noqa: E402

OUT = Path(__file__).resolve().parent / "data" / "kis" / "volume"


def volume(client, keys, tok, code: str, start: date, end: date) -> list[dict]:
    rows, stop = {}, end
    while stop >= start:
        begin = max(start, stop - timedelta(days=90))
        data = get(client, keys, tok, "FHKST03010100", "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", {
            "FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_INPUT_DATE_1": f"{begin:%Y%m%d}",
            "FID_INPUT_DATE_2": f"{stop:%Y%m%d}", "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0"})
        for b in data.get("output2") or []:
            if b.get("stck_bsop_date") and int(b.get("stck_clpr") or 0) > 0:
                rows[b["stck_bsop_date"]] = {"d": b["stck_bsop_date"], "c": int(b["stck_clpr"]), "v": int(b.get("acml_vol") or 0),
                                             "a": int(b.get("acml_tr_pbmn") or 0)}
        stop = begin - timedelta(days=1)
    return [rows[d] for d in sorted(rows)]


def main() -> None:
    keys = load_keys()
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=20) as client:
        tok = token(client, keys)
        for code in sys.argv[1:]:
            path = OUT / f"{code}.json"
            if path.exists():
                continue
            try:
                path.write_text(json.dumps(volume(client, keys, tok, code, date(2025, 10, 1), date.today())), encoding="utf-8")
            except RuntimeError as error:
                print("실패", code, error, flush=True)
                continue
            print("거래량", code, flush=True)


if __name__ == "__main__":
    main()
