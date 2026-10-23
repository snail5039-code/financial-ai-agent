"""10/23 종가 조회 (임시, 읽기 전용). KIS 모의 현재가·지수. 키는 apps/client/dev_keys.env에서 읽고 출력하지 않는다."""
import time

import httpx

env = dict(l.strip().split("=", 1) for l in open(r"C:\puh\multicam\financial-ai-agent\apps\client\dev_keys.env", encoding="utf-8")
           if "=" in l and not l.startswith("#"))
base = "https://openapivts.koreainvestment.com:29443"
tok = httpx.post(base + "/oauth2/tokenP", json={"grant_type": "client_credentials", "appkey": env["KIS_APP_KEY"],
                                                "appsecret": env["KIS_APP_SECRET"]}, timeout=20).json().get("access_token")
assert tok, "토큰 발급 실패"
head = lambda tr: {"authorization": f"Bearer {tok}", "appkey": env["KIS_APP_KEY"], "appsecret": env["KIS_APP_SECRET"],
                   "tr_id": tr, "custtype": "P"}
for code, name in (("0001", "코스피"), ("1001", "코스닥")):
    r = httpx.get(base + "/uapi/domestic-stock/v1/quotations/inquire-index-price", params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": code},
                  headers=head("FHPUP02100000"), timeout=20).json()
    o = r.get("output") or {}
    print(name, r.get("rt_cd"), o.get("bstp_nmix_prpr"), o.get("bstp_nmix_prdy_ctrt"), "시", o.get("bstp_nmix_oprc"), "고", o.get("bstp_nmix_hgpr"), "저", o.get("bstp_nmix_lwpr"))
    time.sleep(1.1)
for code, name in (("098460", "고영"), ("272210", "한화시스템"), ("006400", "삼성SDI"), ("096770", "SK이노베이션"), ("011200", "HMM"),
                   ("028300", "HLB"), ("068270", "셀트리온"), ("033780", "KT&G"), ("000270", "기아"), ("352820", "하이브"), ("000100", "유한양행"), ("021240", "코웨이"),
                   ("373220", "LG에너지솔루션"), ("031980", "피에스케이홀딩스"), ("005940", "NH투자증권")):
    r = httpx.get(base + "/uapi/domestic-stock/v1/quotations/inquire-price", params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": code},
                  headers=head("FHKST01010100"), timeout=20).json()
    o = r.get("output") or {}
    print(name, code, r.get("rt_cd"), o.get("stck_prpr"), o.get("prdy_ctrt"), o.get("stck_oprc"), o.get("stck_hgpr"), o.get("stck_lwpr"))
    time.sleep(1.1)
