"""금융위원회_주식시세정보 (공공데이터포털): 일별 종가와 시가총액.

https://www.data.go.kr/data/15094808/openapi.do
- 하루 늦은 값이다 (영업일 다음 날 오후 갱신). 실시간 가격은 폰이 증권사에서 가져온다
- 이 데이터는 공개 데이터라 여러 사용자에게 같이 보여줘도 된다 (KB 시세와 다름, NFR-05a)
"""

from datetime import date, datetime

import httpx

URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
TIMEOUT_SECONDS = 30


class MarketDataError(Exception):
    pass


def daily_prices(api_key: str, begin: date, end: date, stock_code: str | None = None, rows: int = 10000) -> list[dict]:
    """코스피 종목의 일별 시세. stock_code가 없으면 그 기간 코스피 전체.

    돌려주는 dict: stock_code, stock_name, trade_date, close, market_cap, listed_shares
    """
    params = {
        "serviceKey": api_key, "resultType": "json", "numOfRows": rows, "pageNo": 1, "mrktCls": "KOSPI",
        "beginBasDt": f"{begin:%Y%m%d}", "endBasDt": f"{end:%Y%m%d}",
        **({"likeSrtnCd": stock_code} if stock_code else {}),
    }
    response = httpx.get(URL, params=params, timeout=TIMEOUT_SECONDS)
    try:
        body = response.json()["response"]
    except (ValueError, KeyError) as error:  # 키 오류는 JSON 대신 다른 형식으로 온다
        raise MarketDataError(f"HTTP {response.status_code}: {response.text[:200]}") from error
    if body["header"]["resultCode"] != "00":
        raise MarketDataError(f"{body['header']['resultCode']} {body['header']['resultMsg']}")
    items = body["body"]["items"] or {}
    return [
        {
            "stock_code": item["srtnCd"],
            "stock_name": item["itmsNm"],
            "trade_date": datetime.strptime(item["basDt"], "%Y%m%d").date(),
            "close": int(item["clpr"]),
            "market_cap": int(item["mrktTotAmt"]),
            "listed_shares": int(item["lstgStCnt"]),
        }
        for item in items.get("item", [])
        if not stock_code or item["srtnCd"] == stock_code  # likeSrtnCd는 "포함" 검색이라 정확히 거른다
    ]
