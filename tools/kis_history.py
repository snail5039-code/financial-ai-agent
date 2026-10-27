"""과거 시세 받기 (백테스트용 개발 도구, 읽기 전용). 앱·서버와 따로 돈다.

    python tools/kis_history.py daily 005930 069500 ...      # 일봉(시가·고가·저가·종가) 1년치
    python tools/kis_history.py minute tools/data/need.json   # [[종목, YYYYMMDD], ...] 의 하루치 1분봉

KIS 모의투자 서버(openapivts)의 시세 조회만 쓴다. 키는 apps/client/dev_keys.env에서 읽고 출력하지 않는다. 서버(apps/api)는 키를 쓰지 않는다.
받은 것은 tools/data/kis/ 아래 JSON으로 두고(git 제외), 이미 받은 것은 다시 받지 않는다.
과거 1분봉은 약 1년 전까지만 나온다 (2026-10-27 확인: 2025-10-28 됨, 2025-10-15 0건). 한 번에 120분이라 오전(09:00~11:29)만 받으면 하루에 2번 부른다.
장중에는 앱과 같은 키로 조회가 겹치니 장 마감 뒤에 돌린다.
"""

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kis_mock_check import BASE, headers, load_keys, token  # noqa: E402

OUT = Path(__file__).resolve().parent / "data" / "kis"
GAP = 1.1  # 모의투자는 초당 호출 수가 적다
MINUTE_ENDS = ("112900", "092900")  # 이 시각부터 거꾸로 120분씩 = 09:00~11:29만. 아침 매수를 보는 백테스트라 오전만 받아 호출을 반으로 줄인다 (전 시간대는 153000, 132900을 앞에 더한다)


def get(client: httpx.Client, keys: dict, tok: str, tr_id: str, path: str, params: dict) -> dict:
    data: dict = {}
    for attempt in range(5):
        try:
            r = client.get(f"{BASE}{path}", headers=headers(keys, tok, tr_id), params=params)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        except (httpx.TransportError, ValueError):  # 서버가 연결을 끊는 일이 있다 (2026-10-27 일봉 45종목째). 잠깐 쉬고 다시
            data = {}
        time.sleep(GAP)
        if data.get("rt_cd") == "0":
            return data
        time.sleep(5 * (attempt + 1))  # 초당 한도 초과 등도 잠깐 쉬고 다시
    raise RuntimeError(f"{tr_id} 실패: {data.get('msg_cd')} {(data.get('msg1') or '').strip()}")


def daily(client, keys, tok, code: str, start: date, end: date) -> list[dict]:
    """일봉 [{d, o, h, l, c}] 오래된 것부터. 한 번에 100거래일이라 90일씩 끊어 부른다"""
    bars, stop = {}, end
    while stop >= start:
        begin = max(start, stop - timedelta(days=90))
        data = get(client, keys, tok, "FHKST03010100", "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice", {
            "FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_INPUT_DATE_1": f"{begin:%Y%m%d}",
            "FID_INPUT_DATE_2": f"{stop:%Y%m%d}", "FID_PERIOD_DIV_CODE": "D", "FID_ORG_ADJ_PRC": "0"})
        for b in data.get("output2") or []:
            if b.get("stck_bsop_date") and int(b.get("stck_clpr") or 0) > 0:
                bars[b["stck_bsop_date"]] = {"d": b["stck_bsop_date"], "o": int(b["stck_oprc"]), "h": int(b["stck_hgpr"]),
                                             "l": int(b["stck_lwpr"]), "c": int(b["stck_clpr"])}
        stop = begin - timedelta(days=1)
    return [bars[d] for d in sorted(bars)]


def minute(client, keys, tok, code: str, day: str) -> list[dict]:
    """그날 1분봉 [{t: HHMMSS, o, h, l, c, v}] 시간 순. 다른 날 봉(휴장일이면 앞 거래일)은 버린다"""
    bars = {}
    for end in MINUTE_ENDS:
        data = get(client, keys, tok, "FHKST03010230", "/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice", {
            "FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_INPUT_DATE_1": day, "FID_INPUT_HOUR_1": end,
            "FID_PW_DATA_INCU_YN": "Y", "FID_FAKE_TICK_INCU_YN": ""})
        for b in data.get("output2") or []:
            if b.get("stck_bsop_date") == day and int(b.get("stck_prpr") or 0) > 0:
                bars[b["stck_cntg_hour"]] = {"t": b["stck_cntg_hour"], "o": int(b["stck_oprc"]), "h": int(b["stck_hgpr"]),
                                             "l": int(b["stck_lwpr"]), "c": int(b["stck_prpr"]), "v": int(b.get("cntg_vol") or 0)}
    return [bars[t] for t in sorted(bars)]


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in ("daily", "minute"):
        sys.exit(__doc__)
    keys = load_keys()
    with httpx.Client(timeout=20) as client:
        tok = token(client, keys)
        if sys.argv[1] == "daily":
            (OUT / "daily").mkdir(parents=True, exist_ok=True)
            for code in sys.argv[2:]:
                path = OUT / "daily" / f"{code}.json"
                if path.exists():
                    continue
                try:
                    path.write_text(json.dumps(daily(client, keys, tok, code, date(2025, 10, 1), date.today())), encoding="utf-8")
                except RuntimeError as error:
                    print("실패", code, error, flush=True)
                    continue
                print("일봉", code, flush=True)
        else:
            (OUT / "minute").mkdir(parents=True, exist_ok=True)
            need = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
            for n, (code, day) in enumerate(need, 1):
                path = OUT / "minute" / f"{code}_{day}.json"
                if path.exists():
                    continue
                try:
                    path.write_text(json.dumps(minute(client, keys, tok, code, day)), encoding="utf-8")
                except RuntimeError as error:  # 이 종목·날만 건너뛴다. 다시 돌리면 받지 못한 것부터 이어 받는다
                    print("실패", code, day, error, flush=True)
                    continue
                if n % 50 == 0:
                    print(f"분봉 {n}/{len(need)}", flush=True)


if __name__ == "__main__":
    main()
