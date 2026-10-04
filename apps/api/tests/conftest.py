"""테스트는 개발 DB(invest)가 아니라 invest_test에서만 돈다."""

from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app import config
from app.main import create_app
from app.migrate import migrate

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


@pytest.fixture(scope="session")
def migrated(test_db_url: str) -> str:
    assert migrate(test_db_url) == ["001_init.sql", "002_auth_policy.sql"]
    return test_db_url


@pytest.fixture
def client(migrated: str) -> TestClient:
    return TestClient(create_app(migrated))


PASSWORD = "correct-horse-1"


@pytest.fixture
def user(client: TestClient) -> dict:
    """가입·로그인한 새 회원. 테스트마다 다른 이메일을 쓴다."""
    email = f"{uuid4().hex}@test.kr"
    signup = client.post("/api/auth/signup", json={"email": email, "password": PASSWORD, "agreed_terms": True})
    assert signup.status_code == 201
    token = client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()["token"]
    return {"id": signup.json()["user_id"], "email": email, "headers": {"Authorization": f"Bearer {token}"}}
