"""AI 시험 실행기 배관 (가짜 AI, 비용 0). DB와 python -m app.asof setup/news 가 돼 있어야 한다"""
import os

import pytest

from app import ai_sim


def test_dry_run_flat_window(monkeypatch, capsys):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL 없음")
    monkeypatch.setenv("NEWS_FETCH", "off")
    try:
        ai_sim.run_window("flat", 0.0, True)
    except Exception as error:  # 시험용 스키마가 없으면 건너뜀
        if "simasof" in str(error):
            pytest.skip("python -m app.asof setup 을 먼저")
        raise
    out = capsys.readouterr().out
    assert "[flat]" in out and "비용 $0.00" in out


def test_gather_sees_only_that_morning():
    """앱 분석의 수집 단계가 그날 아침까지의 자료만 보는지 (2026-10-28: 앱 connect가 보기를 덮어써 10월 시세·8월 재무가 섞였던 버그)"""
    from datetime import date
    from types import SimpleNamespace

    from psycopg import connect as pg_connect
    from psycopg.rows import dict_row

    from app import config, sim
    from app.agents import analysis
    from app.agents.state import Context
    from app.asof import asof_url
    if not (os.environ.get("DATABASE_URL") and config.GEMINI_API_KEY):
        pytest.skip("DATABASE_URL·GEMINI_API_KEY 없음")
    base = os.environ["DATABASE_URL"]
    with pg_connect(base, row_factory=dict_row) as conn:
        profile = {"mode": "custom", **conn.execute("SELECT user_id, risk_level, flags FROM investor_profiles LIMIT 1").fetchone()}
    d = date(2026, 5, 4)
    state = ai_sim.make_state(profile, "009150", "삼성전기", "삼성전기 1주 사줘", d, sim.minute_bars("009150", d) or [],
                              sim.daily_bars("009150")["20260504"], 832000, sim.Book(cash=10_000_000), [("20260430", 100.0)] * 25, 100.0, True, 911000) | {"qty": 1}
    got = analysis.gather_node(state, SimpleNamespace(context=Context(asof_url(base, "2026-05-04"))))
    assert "평균은 2026-04-30까지" in got["sources"]["trend:009150"]["content"]
    assert not any(k.startswith("fin:2026") and k[4:12] >= "20260504" for k in got["sources"])
    assert all(v.get("as_of") is None or str(v["as_of"])[:10] < "2026-05-04" for k, v in got["sources"].items() if k.startswith(("dart", "news")))
