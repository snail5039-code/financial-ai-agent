import psycopg

from app import config


def connect(url: str | None = None) -> psycopg.Connection:
    # ponytail: 요청마다 새 연결. 3단계(PostgresSaver)에서 psycopg_pool로 바꾼다
    url = url or config.DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL이 비어 있습니다. apps/api/.env를 확인하세요.")
    return psycopg.connect(url, connect_timeout=3)
