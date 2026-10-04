"""테스트는 개발 DB(invest)가 아니라 invest_test에서만 돈다."""

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app import config

TEST_DB = "invest_test"


@pytest.fixture(scope="session")
def test_db_url() -> str:
    if not config.DATABASE_URL:
        pytest.skip("DATABASE_URL이 없습니다 (apps/api/.env)")
    params = conninfo_to_dict(config.DATABASE_URL)
    admin_url = make_conninfo(**{**params, "dbname": "postgres"})
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)")
        conn.execute(f"CREATE DATABASE {TEST_DB}")
    return make_conninfo(**{**params, "dbname": TEST_DB})
