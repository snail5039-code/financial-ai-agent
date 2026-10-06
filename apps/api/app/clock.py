from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9), name="KST")


def now() -> datetime:
    """지금 한국 시각. 장 운영 시간·만료 판단에 쓴다 (테스트에서 바꿔 끼울 수 있게 한 곳에 둔다)."""
    return datetime.now(KST)
