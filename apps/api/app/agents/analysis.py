"""분석 그래프: 투자 AI ↔ 검증 AI (docs/plan/04-graph-design.md 4장).

    find_stock → check_target → get_account → gather → invest_agent → verify_agent ─┬─ record → END
                                                              ↑                      │
                                                              └── 반려, 수정 2번 미만 ─┘

- gather: 출처(공시·재무·시세·계좌)를 모으고 지표를 코드로 계산한다. 출처마다 ID를 붙인다
- invest_agent: 투자 AI가 제안서를 쓴다. 성향에 맞지 않는 행동이면 코드가 '관찰'로 바꾼다
- verify_agent: 검증 AI는 투자 AI의 입력을 보지 않는다. 제안서의 근거·출처 ID만 받아서
  출처 원문을 DB에서 다시 읽고, 지표를 다시 계산하고, 코드 검사를 먼저 한 뒤 판정한다 (FR-17)
- record: 제안서와 판정을 저장하고 답을 만든다 (저장은 이 노드에서만)
"""

import json
from datetime import datetime, timedelta

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.agents import llm
from app.agents.interrupts import pause
from app.agents.query import SOURCE_LABELS, as_of, end_if_answered, find_stock_node, latest_snapshot, won
from app.agents.state import Context, InvestState
from app.clock import KST
from app.db import connect
from app.functions import metrics
from app.functions.profile import LABELS
from app.functions.suitability import allowed_actions, stock_risk_grade
from app.integrations.opendart import disclosure_url

MAX_REVISIONS = 2
MAX_ANALYSES_PER_DAY = 20  # Gemini 비용 관리 (NFR-14)
SEARCH_RESULTS = 4
RECENT_DISCLOSURES = 5
SNAPSHOT_MAX_AGE = timedelta(minutes=30)

NOT_TARGET_MESSAGE = "{name}은(는) 아직 분석 대상이 아니에요. 지금은 코스피 시가총액 상위 30개 종목만 분석해요."
LIMIT_MESSAGE = f"오늘 분석은 {MAX_ANALYSES_PER_DAY}번까지 할 수 있어요. 내일 다시 시도해 주세요."
ACTION_LABELS = {"buy": "매수 검토", "sell": "매도 검토", "hold": "보유", "watch": "관찰"}
VERDICT_LABELS = {"approve": "승인", "conditional": "조건부 승인", "reject": "반려", "user_judgement": "사용자 판단 필요"}
CLAIM_LABELS = {"fact": "사실", "calc": "계산", "inference": "추론", "opinion": "의견"}
FLAG_GUIDES = {
    "vulnerable": "65세 이상이다. 손실 가능성과 불리한 점을 먼저 쓴다.",
    "no_buy_proposals": "생활비나 빌린 돈으로 투자한다. 매수를 제안하지 않는다.",
    "high_interest_debt": "고금리 빚을 갚는 중이다. 빚을 먼저 갚는 것이 확실한 수익이라는 점을 위험에 쓴다.",
    "chases_hot_stocks": "급등주를 바로 사는 경향이 있다. 최근 가격 흐름의 위험을 쓴다.",
    "quiz_missed": "분산 투자와 매매 비용(수수료·세금) 개념을 짧게 설명한다.",
}
GENERAL_MODE_GUIDE = "일반 모드다 (성향 퀴즈 안 함). 판단하지 말고 사실·지표·장단점·위험만 쓴다. 의견(opinion) 근거는 쓰지 않는다."


# ---------- 출처 ----------
# 출처 ID 규칙
#   dart:{접수번호}         공시 (제목·접수일)          dart:{접수번호}#{조각번호}  정기보고서 본문 조각
#   fin:{접수번호}          그 공시의 주요 재무 계정     price:{종목}:{날짜}        그날 종가·시가총액 (하루 늦은 공개 데이터)
#   quote:{종목}            폰이 증권사에서 받은 현재가  snapshot                  폰이 보낸 내 계좌 요약

def load_sources(conn, ids: list[str], state: InvestState) -> dict[str, dict]:
    """출처 ID → {kind, title, url, as_of, content}. 없는 ID는 결과에서 빠진다 (검증에서 '없는 출처'로 잡힘)."""
    found = {}
    for source_id in dict.fromkeys(ids):
        source = load_source(conn, source_id, state)
        if source:
            found[source_id] = source
    return found


def load_source(conn, source_id: str, state: InvestState) -> dict | None:
    kind, _, rest = source_id.partition(":")
    if kind == "dart" and "#" in rest:
        rcept_no, seq = rest.split("#", 1)
        row = conn.execute(
            "SELECT d.title, d.url, d.filed_at, c.section, c.content FROM disclosure_chunks c"
            " JOIN disclosures d USING (rcept_no) WHERE c.rcept_no = %s AND c.seq::text = %s", (rcept_no, seq),
        ).fetchone()
        return row and {"kind": "dart", "title": f"{row['title']} · {row['section']}", "url": row["url"],
                        "as_of": str(row["filed_at"]), "content": row["content"]}
    if kind == "dart":
        row = conn.execute("SELECT title, url, filed_at FROM disclosures WHERE rcept_no = %s", (rest,)).fetchone()
        return row and {"kind": "dart", "title": row["title"], "url": row["url"],
                        "as_of": str(row["filed_at"]), "content": f"공시 제목: {row['title']} (접수일 {row['filed_at']})"}
    if kind == "fin":
        rows = conn.execute(
            "SELECT bsns_year, reprt_code, fs_div, account, amount, prev_amount FROM financials"
            " WHERE rcept_no = %s AND fs_div = 'CFS' ORDER BY account", (rest,),
        ).fetchall()
        if not rows:
            return None
        lines = [f"{r['account']}: 이번 기간 {fmt_amount(r['amount'])}, 전년 같은 기간 {fmt_amount(r['prev_amount'])}"
                 for r in rows]
        return {"kind": "dart", "title": f"OpenDART 주요 재무 ({rows[0]['bsns_year']}년 사업보고서, 연결)",
                "url": disclosure_url(rest), "as_of": None, "content": "\n".join(lines)}
    if kind == "price":
        code, _, day = rest.partition(":")
        row = conn.execute("SELECT close, market_cap FROM stock_prices WHERE stock_code = %s AND trade_date::text = %s",
                           (code, day)).fetchone()
        return row and {"kind": "price", "title": f"{day} 종가 (금융위원회_주식시세정보)", "url": None, "as_of": day,
                        "content": f"종가 {won(row['close'])}, 시가총액 {won(row['market_cap'])}"}
    if kind == "quote" and state.get("prices"):
        price = state["prices"][0]
        return {"kind": "price", "title": "현재가 (앱 실시간 조회)", "url": None, "as_of": price["as_of"],
                "content": f"현재가 {won(price['price'])}"}
    if source_id == "snapshot" and state.get("snapshot"):
        snapshot = state["snapshot"]
        held = [h for h in snapshot["holdings"] if h["stock_code"] == state["stock_code"]]
        holding = (f"이 종목 {held[0]['qty']:,}주, 평균 매입가 {won(held[0]['avg_price'])}" if held else "이 종목 없음")
        return {"kind": "snapshot", "title": f"내 계좌 ({SOURCE_LABELS[snapshot['source']]})", "url": None,
                "as_of": snapshot["fetched_at"], "content": f"현금 {won(snapshot['cash_krw'])}, {holding}"}
    return None


def fmt_amount(value: int | None) -> str:
    return "없음" if value is None else won(value)


# ---------- 지표 (코드 계산) ----------

def latest_annual_financials(conn, code: str) -> dict[str, dict]:
    """가장 최근 사업보고서(연결)의 계정 → {amount, prev_amount, rcept_no}."""
    rows = conn.execute(
        "SELECT account, amount, prev_amount, rcept_no FROM financials"
        " WHERE stock_code = %s AND reprt_code = '11011' AND fs_div = 'CFS'"
        " AND bsns_year = (SELECT max(bsns_year) FROM financials WHERE stock_code = %s AND reprt_code = '11011')",
        (code, code),
    ).fetchall()
    accounts = {}
    for row in rows:
        name = "당기순이익" if row["account"].startswith("당기순이익") else row["account"]
        accounts.setdefault(name, row)
    return accounts


def compute_metrics(conn, code: str) -> list[dict]:
    """DB의 원 자료로 지표를 계산한다. gather와 verify_agent가 따로 부른다 (검증은 다시 계산)."""
    closes = conn.execute(
        "SELECT trade_date, close, market_cap FROM stock_prices WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 21",
        (code,),
    ).fetchall()[::-1]
    fin = latest_annual_financials(conn, code)
    price_id = f"price:{code}:{closes[-1]['trade_date']}" if closes else None
    fin_id = f"fin:{next(iter(fin.values()))['rcept_no']}" if fin else None

    def value_of(account: str, field: str = "amount"):
        return (fin.get(account) or {}).get(field)

    result = []
    market_cap = closes[-1]["market_cap"] if closes else None
    for metric_id, account, function in (("per", "당기순이익", metrics.per), ("pbr", "자본총계", metrics.pbr)):
        if market_cap is None or value_of(account) is None:
            result.append(metrics.metric(metric_id, None, "배", "", [], "시세나 재무 자료가 없음"))
        else:
            result.append(function(market_cap, value_of(account), [price_id, fin_id]))
    if value_of("부채총계") is None or value_of("자본총계") is None:
        result.append(metrics.metric("debt_ratio", None, "%", "", [], "재무 자료가 없음"))
    else:
        result.append(metrics.debt_ratio(value_of("부채총계"), value_of("자본총계"), [fin_id]))
    for metric_id, account in (("revenue_yoy", "매출액"), ("op_income_yoy", "영업이익")):
        current, previous = value_of(account), value_of(account, "prev_amount")
        if current is None or previous is None:
            result.append(metrics.metric(metric_id, None, "%", "", [], "재무 자료가 없음"))
        else:
            result.append(metrics.yoy_growth(metric_id, account, current, previous, [fin_id]))
    result.append(metrics.volatility_20d([row["close"] for row in closes], [price_id] if price_id else []))
    return result


def metric_line(metric: dict) -> str:
    if metric["value"] is None:
        return f"- {metric['metric_id']}: 계산 불가 ({metric['reason']})"
    return (f"- {metric['metric_id']}: {metric['value']}{metric['unit']} "
            f"(계산식: {metric['formula']}, 출처: {', '.join(metric['inputs'])})")


# ---------- 코드 검사 (검증 AI 전에) ----------

def code_checks(proposal: dict, known_sources: dict, gathered_metrics: list[dict], recomputed: list[dict]) -> list[dict]:
    """AI 없이 확실히 잡을 수 있는 것: 출처·지표 ID가 실제로 있는지, 사실·계산에 출처가 붙었는지,
    지표를 다시 계산하면 같은 값인지, 반대 근거·위험이 있는지. 하나라도 fail이면 승인하지 않는다."""
    checks = []
    metric_ids = {m["metric_id"] for m in recomputed if m["value"] is not None}
    for number, claim in enumerate(proposal["claims"]):
        problems = []
        if claim["type"] in ("fact", "calc") and not claim["source_ids"]:
            problems.append("사실·계산 근거인데 출처가 없음")
        if missing := [s for s in claim["source_ids"] if s not in known_sources]:
            problems.append(f"없는 출처 ID: {', '.join(missing)}")
        if claim["type"] == "calc" and not claim["metric_ids"]:
            problems.append("계산 근거인데 지표 ID가 없음")
        if unknown := [m for m in claim["metric_ids"] if m not in metric_ids]:
            problems.append(f"없거나 계산할 수 없는 지표 ID: {', '.join(unknown)}")
        checks.append({"target": f"claim:{number}", "result": "fail" if problems else "pass",
                       "detail": "; ".join(problems) or "출처·지표 ID 확인", "source_ids": claim["source_ids"]})

    before = {m["metric_id"]: m["value"] for m in gathered_metrics}
    changed = [m["metric_id"] for m in recomputed if before.get(m["metric_id"]) != m["value"]]
    checks.append({"target": "metrics", "result": "fail" if changed else "pass",
                   "detail": f"다시 계산한 값이 다름: {', '.join(changed)}" if changed else "지표를 다시 계산해 같은 값 확인",
                   "source_ids": []})
    for field, label in (("counter_arguments", "반대 근거"), ("risks", "위험")):
        checks.append({"target": field, "result": "pass" if proposal[field] else "fail",
                       "detail": f"{label} {len(proposal[field])}개" if proposal[field] else f"{label}가 없음",
                       "source_ids": []})
    return checks


# ---------- AI에게 넘길 글 ----------

def user_lines(state: InvestState) -> list[str]:
    if state["mode"] != "custom":
        return [GENERAL_MODE_GUIDE]
    lines = [f"성향: {state['risk_level']}단계 {LABELS[state['risk_level']]}"]
    return lines + [FLAG_GUIDES[flag] for flag in state.get("flags") or [] if flag in FLAG_GUIDES]


def source_lines(sources: dict) -> list[str]:
    return [f"- {sid} | {s['title']} | 기준 {s['as_of'] or '미확인'}\n  {s['content']}" for sid, s in sources.items()]


def invest_context(state: InvestState) -> str:
    parts = [
        f"[요청] {state['query']}",
        f"[종목] {state['stock_name']}({state['stock_code']}), 위험등급 {state['risk_grade']}등급",
        "[사용자]\n" + "\n".join(user_lines(state)),
        f"[허용 행동] {', '.join(state['allowed_actions'])}",
        "[자료]\n" + "\n".join(source_lines(state["sources"])),
        "[지표] (코드가 계산한 값. 이 값만 쓴다)\n" + "\n".join(metric_line(m) for m in state["metrics"]),
    ]
    if state.get("verifications"):
        last = state["verifications"][-1]
        parts.append("[검증 AI 반박] 아래를 고쳐 다시 써라\n" + "\n".join(f"- {c}" for c in last["challenges"]))
    return "\n\n".join(parts)


def verify_context(state: InvestState, proposal: dict, reloaded: dict, recomputed: list[dict], checks: list[dict]) -> str:
    """검증 AI에게는 제안서의 행동·근거·출처 ID와, 다시 읽은 원문·다시 계산한 지표만 준다.
    투자 AI의 지시문·입력 자료 목록은 주지 않는다."""
    claims = [f"{n}. ({c['type']}) {c['text']} | 출처: {', '.join(c['source_ids']) or '없음'}"
              f" | 지표: {', '.join(c['metric_ids']) or '없음'}" for n, c in enumerate(proposal["claims"])]
    return "\n\n".join([
        f"[종목] {state['stock_name']}({state['stock_code']}), 위험등급 {state['risk_grade']}등급",
        "[사용자]\n" + "\n".join(user_lines(state)),
        f"[제안] 행동: {proposal['action']}",
        "[근거]\n" + "\n".join(claims),
        "[반대 근거]\n" + "\n".join(f"- {x}" for x in proposal["counter_arguments"]),
        "[위험]\n" + "\n".join(f"- {x}" for x in proposal["risks"]),
        "[판단이 틀리는 조건]\n" + "\n".join(f"- {x}" for x in proposal["invalid_if"]),
        "[원문] (출처 ID로 다시 읽은 것)\n" + "\n".join(source_lines(reloaded)),
        "[다시 계산한 지표]\n" + "\n".join(metric_line(m) for m in recomputed),
        "[코드 검사]\n" + "\n".join(f"- {c['target']}: {c['result']} ({c['detail']})" for c in checks),
    ])


# ---------- 노드 ----------

def check_target_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    with connect(runtime.context.database_url, row_factory=dict_row) as conn:
        stock = conn.execute("SELECT is_target FROM stocks WHERE code = %s", (state["stock_code"],)).fetchone()
        if not stock["is_target"]:
            return {"answer": NOT_TARGET_MESSAGE.format(name=state["stock_name"])}
        today_count = conn.execute(
            "SELECT count(*) AS n FROM proposals WHERE user_id = %s AND created_at >= date_trunc('day', now())",
            (state["user_id"],),
        ).fetchone()["n"]
    if today_count >= MAX_ANALYSES_PER_DAY:
        return {"answer": LIMIT_MESSAGE}
    return {}


def get_account_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    """앱이면 폰에 잔고·현재가를 부탁하고, 웹이면 최근 스냅샷을 쓴다. 웹은 실시간 현재가 없이 전일 종가로 본다."""
    if state["client"] == "web":
        with connect(runtime.context.database_url, row_factory=dict_row) as conn:
            snapshot = latest_snapshot(conn, state["user_id"])
        if snapshot is None or datetime.now(KST) - snapshot["fetched_at"] > SNAPSHOT_MAX_AGE:
            return {"snapshot": None, "prices": None}  # 계좌 없이도 분석은 한다 (보유 여부는 모름)
        return {"snapshot": {**snapshot, "fetched_at": snapshot["fetched_at"].isoformat(), "source": "server"}}

    reply = pause("fetch", needs=[{"type": "balance"}, {"type": "price", "stock_code": state["stock_code"]}])
    if reply.get("error"):
        return {"answer": f"증권사 조회에 실패했어요 ({reply['error']}). 잠시 후 다시 시도해 주세요."}
    price = next((p for p in reply.get("prices") or [] if p["stock_code"] == state["stock_code"]), None)
    return {"snapshot": reply.get("balance") and {**reply["balance"], "source": "app"},
            "prices": [price] if price else None}


def gather_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    code = state["stock_code"]
    with connect(runtime.context.database_url, row_factory=dict_row) as conn:
        ids = []
        latest = conn.execute("SELECT trade_date FROM stock_prices WHERE stock_code = %s ORDER BY trade_date DESC LIMIT 1",
                              (code,)).fetchone()
        if latest:
            ids.append(f"price:{code}:{latest['trade_date']}")
        fin = latest_annual_financials(conn, code)
        if fin:
            ids.append(f"fin:{next(iter(fin.values()))['rcept_no']}")
        ids += [f"dart:{row['rcept_no']}" for row in conn.execute(
            "SELECT rcept_no FROM disclosures WHERE stock_code = %s ORDER BY filed_at DESC LIMIT %s",
            (code, RECENT_DISCLOSURES))]
        if conn.execute("SELECT 1 FROM disclosure_chunks c JOIN disclosures d USING (rcept_no)"
                        " WHERE d.stock_code = %s LIMIT 1", (code,)).fetchone():
            vector = str(llm.embed_query(f"{state['stock_name']} {state['query']}"))
            ids += [f"dart:{row['rcept_no']}#{row['seq']}" for row in conn.execute(
                "SELECT c.rcept_no, c.seq FROM disclosure_chunks c JOIN disclosures d USING (rcept_no)"
                " WHERE d.stock_code = %s ORDER BY c.embedding <=> %s::vector LIMIT %s",
                (code, vector, SEARCH_RESULTS))]
        if state.get("prices"):
            ids.append(f"quote:{code}")
        if state.get("snapshot"):
            ids.append("snapshot")
        sources = load_sources(conn, ids, state)
        found_metrics = compute_metrics(conn, code)

    holds = bool(state.get("snapshot")) and any(h["stock_code"] == code for h in state["snapshot"]["holdings"])
    grade = stock_risk_grade(code)
    return {
        "sources": sources, "metrics": json.loads(json.dumps(found_metrics, default=str)),
        "risk_grade": grade, "allowed_actions": allowed_actions(state["mode"], state.get("risk_level"),
                                                                state.get("flags") or [], grade, holds),
        "verifications": [], "revision_round": 0,
    }


def invest_agent_node(state: InvestState) -> dict:
    draft = llm.write_proposal(invest_context(state)).model_dump()
    if draft["action"] not in state["allowed_actions"]:
        # 성향 규칙은 AI가 아니라 코드가 지킨다
        draft["risks"].append(f"성향 규칙에 따라 '{ACTION_LABELS[draft['action']]}' 대신 '관찰'로 바꿨어요.")
        draft["action"] = "watch"
    return {"proposal": {**draft, "stock_code": state["stock_code"], "stock_name": state["stock_name"],
                         "qty": None, "limit_price": None, "user_directed": False}}


def verify_agent_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    proposal = state["proposal"]
    cited = [sid for claim in proposal["claims"] for sid in claim["source_ids"]]
    with connect(runtime.context.database_url, row_factory=dict_row) as conn:
        reloaded = load_sources(conn, cited, state)  # 투자 AI가 본 자료가 아니라 원문을 다시 읽는다
        recomputed = json.loads(json.dumps(compute_metrics(conn, state["stock_code"]), default=str))
    checks = code_checks(proposal, reloaded, state["metrics"], recomputed)
    draft = llm.verify_proposal(verify_context(state, proposal, reloaded, recomputed, checks)).model_dump()

    failed = [c for c in checks if c["result"] == "fail"]
    if failed and draft["verdict"] in ("approve", "conditional"):
        draft["verdict"] = "reject"  # 코드 검사에서 틀린 것이 나오면 AI가 승인해도 반려
        draft["challenges"] += [f"{c['target']}: {c['detail']}" for c in failed]
    round_number = state["revision_round"]
    if draft["verdict"] == "reject" and round_number >= MAX_REVISIONS:
        draft["verdict"] = "user_judgement"  # 2번 고쳐도 합의가 안 되면 사용자가 판단
        draft["summary"] = f"{MAX_REVISIONS}번 수정했지만 검증을 통과하지 못했어요. " + draft["summary"]
    verification = {**draft, "checks": checks + draft["checks"], "round": round_number}
    return {"verifications": state["verifications"] + [verification], "revision_round": round_number + 1}


def route_after_verify(state: InvestState) -> str:
    return "invest_agent" if state["verifications"][-1]["verdict"] == "reject" else "record"


def record_node(state: InvestState, runtime: Runtime[Context]) -> dict:
    proposal, verifications = state["proposal"], state["verifications"]
    data_as_of = max((s["as_of"] for s in state["sources"].values() if s["as_of"]), default=None)
    sources = [{"source_id": sid, **{k: v for k, v in s.items() if k != "content"}} for sid, s in state["sources"].items()]
    with connect(runtime.context.database_url) as conn:
        proposal_id = conn.execute(
            "INSERT INTO proposals (user_id, thread_id, stock_code, action, qty, limit_price, claims, sources, metrics,"
            " counter_arguments, risks, invalid_if, user_directed, data_as_of)"
            " VALUES (%s, %s, %s, %s, NULL, NULL, %s, %s, %s, %s, %s, %s, false, %s) RETURNING id",
            (state["user_id"], state["thread_id"], proposal["stock_code"], proposal["action"],
             Jsonb(proposal["claims"]), Jsonb(sources), Jsonb(state["metrics"]), Jsonb(proposal["counter_arguments"]),
             Jsonb(proposal["risks"]), Jsonb(proposal["invalid_if"]), data_as_of),
        ).fetchone()[0]
        for v in verifications:
            conn.execute(
                "INSERT INTO verifications (proposal_id, round, verdict, checks, challenges, conditions, disagreements,"
                " risk_fit, summary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (proposal_id, v["round"], v["verdict"], Jsonb(v["checks"]), Jsonb(v["challenges"]),
                 Jsonb(v["conditions"]), Jsonb(v["disagreements"]), v["risk_fit"], v["summary"]),
            )
    return {"answer": format_analysis(state)}


# ---------- 답 ----------

def format_analysis(state: InvestState) -> str:
    proposal, verification, sources = state["proposal"], state["verifications"][-1], state["sources"]
    lines = [f"{state['stock_name']}({state['stock_code']}) 분석 · 검증: {VERDICT_LABELS[verification['verdict']]}"]
    if state["mode"] != "custom":
        lines.append("일반 모드라 사라·말라 판단은 하지 않고 정보만 정리했어요. 성향 퀴즈를 하면 맞춤 제안을 받을 수 있어요.")
    else:
        lines.append(f"제안: {ACTION_LABELS[proposal['action']]}")

    lines.append("\n근거")
    for claim in proposal["claims"]:
        cited = ", ".join(sources[s]["title"] for s in claim["source_ids"] if s in sources)
        lines.append(f"- ({CLAIM_LABELS[claim['type']]}) {claim['text']}" + (f" [{cited}]" if cited else ""))
    for title, items in (("반대 근거", proposal["counter_arguments"]), ("위험", proposal["risks"]),
                         ("이런 경우 판단이 틀린 것", proposal["invalid_if"])):
        lines += [f"\n{title}"] + [f"- {item}" for item in items]

    lines.append("\n지표 (코드 계산)")
    for metric in state["metrics"]:
        value = f"{metric['value']}{metric['unit']}" if metric["value"] is not None else f"계산 불가 ({metric['reason']})"
        lines.append(f"- {METRIC_NAMES.get(metric['metric_id'], metric['metric_id'])}: {value}")

    lines.append(f"\n검증 AI: {verification['summary']}")
    lines += [f"- 조건: {c}" for c in verification["conditions"]]
    lines += [f"- 의견 차이: {d}" for d in verification["disagreements"]]

    lines.append("\n출처 (근거와 지표에 쓴 것)")
    used = [sid for claim in proposal["claims"] for sid in claim["source_ids"]]
    used += [sid for metric in state["metrics"] if metric["value"] is not None for sid in metric["inputs"]]
    shown = set()
    for source in (sources[sid] for sid in dict.fromkeys(used) if sid in sources):
        if (source["title"], source["url"]) in shown:
            continue  # 같은 보고서의 여러 조각은 한 번만
        shown.add((source["title"], source["url"]))
        when = f", {source_time(source['as_of'])}" if source["as_of"] else ""
        lines.append(f"- {source['title']}{when}" + (f" {source['url']}" if source["url"] else ""))
    if proposal["action"] in ("buy", "sell"):
        lines.append("\n주문으로 이어가는 기능은 다음 단계에서 연결돼요.")
    lines.append("\n투자 판단과 책임은 본인에게 있어요. 이 분석은 참고용이며 손실이 날 수 있어요.")
    return "\n".join(lines)


def source_time(value: str) -> str:
    """날짜만 있으면 그대로, 시각까지 있으면 "10-05 17:39 기준"."""
    return as_of(value) if "T" in value else f"{value} 기준"


METRIC_NAMES = {"per": "PER", "pbr": "PBR", "debt_ratio": "부채비율", "revenue_yoy": "매출 전년 대비",
                "op_income_yoy": "영업이익 전년 대비", "volatility_20d": "20일 변동성(연 환산)"}


# ---------- 그래프 ----------

def build_analysis_graph():
    builder = StateGraph(InvestState, context_schema=Context)
    builder.add_node("find_stock", find_stock_node)
    builder.add_node("check_target", check_target_node)
    builder.add_node("get_account", get_account_node)
    builder.add_node("gather", gather_node)
    builder.add_node("invest_agent", invest_agent_node)
    builder.add_node("verify_agent", verify_agent_node)
    builder.add_node("record", record_node)

    builder.add_edge(START, "find_stock")
    builder.add_conditional_edges("find_stock", end_if_answered("check_target"), ["check_target", END])
    builder.add_conditional_edges("check_target", end_if_answered("get_account"), ["get_account", END])
    builder.add_conditional_edges("get_account", end_if_answered("gather"), ["gather", END])
    builder.add_edge("gather", "invest_agent")
    builder.add_edge("invest_agent", "verify_agent")
    builder.add_conditional_edges("verify_agent", route_after_verify, ["invest_agent", "record"])
    builder.add_edge("record", END)
    return builder.compile()
