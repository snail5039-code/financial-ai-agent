"""Thin client for the 금융감독원 OpenDART public disclosure API.

Only the two calls Company Detail needs: mapping a stock code to OpenDART's
own 8-digit corp_code (`corpCode.xml`, downloaded once and cached to disk —
the mapping is large and essentially static), then listing that company's
recent disclosures (`list.json`).

This is the only module in `apps/api` that makes a real outbound network
call. Everything else in this app is local-only by design (see AGENTS.md) —
keep it that way: no other integration belongs here without the same
"read-only, publicly available, no account/money involved" property OpenDART
has.
"""

import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import httpx

OPENDART_BASE_URL = "https://opendart.fss.or.kr/api"
CORP_CODE_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "opendart_corp_codes.xml"
REQUEST_TIMEOUT_SECONDS = 15

# OpenDART's own status codes (payload["status"]). "000" is success; "013" is
# a normal empty result ("조회된 데이타가 없습니다"), not an error. Anything
# else (auth failure, rate limit, bad params, ...) is a real error.
STATUS_OK = "000"
STATUS_NO_DATA = "013"


class OpenDartError(Exception):
    """Any non-success response from OpenDART, or a corp_code we can't find."""


async def _download_corp_codes(api_key: str) -> bytes:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(f"{OPENDART_BASE_URL}/corpCode.xml", params={"crtfc_key": api_key})
        response.raise_for_status()
        return response.content


async def _ensure_corp_code_cache(api_key: str) -> Path:
    """`corpCode.xml` is a zip of every listed company's stock_code<->corp_code
    mapping. It changes rarely, so once downloaded it's cached indefinitely —
    delete the file to force a refresh."""
    if CORP_CODE_CACHE_PATH.exists():
        return CORP_CODE_CACHE_PATH

    raw_zip = await _download_corp_codes(api_key)
    try:
        with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
            xml_bytes = archive.read("CORPCODE.xml")
    except zipfile.BadZipFile as exc:
        # A bad/expired key makes corpCode.xml return an XML error body
        # instead of a zip file — surface that instead of a confusing
        # "not a zip file" trace.
        raise OpenDartError(f"OpenDART corpCode.xml did not return a zip file: {raw_zip[:200]!r}") from exc

    CORP_CODE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CORP_CODE_CACHE_PATH.write_bytes(xml_bytes)
    return CORP_CODE_CACHE_PATH


async def get_corp_code(stock_code: str, api_key: str) -> str:
    path = await _ensure_corp_code_cache(api_key)
    for _, elem in ET.iterparse(path):
        if elem.tag != "list":
            continue
        if (elem.findtext("stock_code") or "").strip() == stock_code:
            corp_code = elem.findtext("corp_code")
            elem.clear()
            if corp_code:
                return corp_code
        elem.clear()
    raise OpenDartError(f"stock_code {stock_code!r} not found in OpenDART's corp code list")


async def fetch_recent_disclosures(stock_code: str, api_key: str, count: int = 5) -> list[dict]:
    """Returns up to `count` of the company's most recent disclosures, most
    recent first — each a dict with (at least) report_nm, rcept_no, rcept_dt,
    flr_nm, as OpenDART's `list.json` returns them."""
    corp_code = await get_corp_code(stock_code, api_key)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(
            f"{OPENDART_BASE_URL}/list.json",
            params={"crtfc_key": api_key, "corp_code": corp_code, "page_no": 1, "page_count": count},
        )
        response.raise_for_status()
        payload = response.json()

    status = payload.get("status")
    if status == STATUS_NO_DATA:
        return []
    if status != STATUS_OK:
        raise OpenDartError(f"OpenDART list.json returned status {status}: {payload.get('message')}")

    return payload.get("list", [])
