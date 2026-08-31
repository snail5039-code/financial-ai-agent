from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9), name="KST")


def now_kst_iso() -> str:
    """Return the current time as a KST ISO 8601 string.

    Used only for local response metadata. It is not a market data timestamp.
    """
    return datetime.now(KST).isoformat()
