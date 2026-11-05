"""종가 직전(15:00~15:30) 1분봉 받기 (백테스트용, 읽기 전용). 앱이 15:20쯤 사는 값을 재현하려는 것.

    python tools/kis_late.py 069500   # 하루마다 종가 직전 1분봉 → tools/data/kis/late/<종목>.json {날짜: [봉]}
"""

import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kis_history import get  # noqa: E402
from kis_mock_check import load_keys, token  # noqa: E402

OUT = Path(__file__).resolve().parent / "data" / "kis" / "late"


def main() -> None:
    code = sys.argv[1]
    days = sorted(b["d"] for b in json.loads((OUT.parent / "daily" / f"{code}.json").read_text(encoding="utf-8")) if b["d"] >= "20251028")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{code}.json"
    res = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    keys = load_keys()
    with httpx.Client(timeout=20) as client:
        tok = token(client, keys)
        for day in days:
            if day in res:
                continue
            try:
                data = get(client, keys, tok, "FHKST03010230", "/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice", {
                    "FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code, "FID_INPUT_DATE_1": day, "FID_INPUT_HOUR_1": "153000",
                    "FID_PW_DATA_INCU_YN": "Y", "FID_FAKE_TICK_INCU_YN": ""})
            except RuntimeError as error:
                print("실패", day, error, flush=True)
                continue
            res[day] = [{"t": b["stck_cntg_hour"], "c": int(b["stck_prpr"])} for b in data.get("output2") or []
                        if b.get("stck_bsop_date") == day and b["stck_cntg_hour"] >= "150000" and int(b.get("stck_prpr") or 0) > 0]
            path.write_text(json.dumps(res), encoding="utf-8")


if __name__ == "__main__":
    main()
