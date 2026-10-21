"""Study 2 run collector: one row per run with the commission ledger (primary), dollar-diff omission (secondary),
benchmark outcome and cost (agent + simulator from token usage, plus harness checks from harness.jsonl).

Prices (USD per MTok: input, output, cache read), checked 2026-10-21 on the Anthropic and OpenAI pricing pages.
Goal 3's collect.py is left untouched (its Sonnet cache-read price is 0.20; the current price is 0.10).

Usage: python -m trustcurve.study2.collect2 <results.json> <meta.json> <config_id> <sim_label> <out.csv>
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from trustcurve.collect import _usage
from trustcurve.study2.forecast import BASIC_LIMIT
from trustcurve.study2.ledger import ledger_for_run

PRICES2 = {"claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-sonnet-5-5": (2.00, 10.00, 0.10),
           "claude-opus-5-5": (4.00, 20.00, 0.20), "gpt-6.1-sol": (2.00, 10.00, 0.10),
           "gpt-6-luna": (0.10, 0.50, 0.01)}
LONG2 = {"claude-haiku-5-5": (0.50, 2.50, 0.05)}
CACHE_WRITE_MULT = 1.25


def cost_of(t: dict, model: str) -> float | None:
    m = model.split("/")[-1]
    if m not in PRICES2:
        return None
    pin, pout, pc = PRICES2[m]
    lin, lout, _ = LONG2.get(m, (pin, pout, pc))
    return (t["inp"] * pin + t["out"] * pout + t["long_in"] * lin + t["long_out"] * lout
            + t["cached"] * pc + t["cache_write"] * pin * CACHE_WRITE_MULT) / 1e6


def harness_cost(harness_path: Path) -> tuple[float, int, int]:
    """Total harness check cost, number of checks and number of blocks in one run directory."""
    if not harness_path.exists():
        return 0.0, 0, 0
    tot, n, blocked = 0.0, 0, 0
    for line in harness_path.read_text().splitlines():
        r = json.loads(line)
        u = r.get("usage") or {}
        if u:
            n += 1
            m = (r.get("checker") or "").split("/")[-1]
            if m in PRICES2:
                pin, pout, _ = PRICES2[m]
                tot += (int(u.get("prompt_tokens") or 0) * pin + int(u.get("completion_tokens") or 0) * pout) / 1e6
        blocked += r.get("allowed") is False
    return tot, n, blocked


def collect_runs(results_path, meta_path, config_id, sim_label) -> list[dict]:
    from tau2.data_model.message import AssistantMessage, ToolMessage, UserMessage
    from tau2.data_model.tasks import Task

    from trustcurve.dollar_diff import dollar_diff, gold_and_agent_dbs, initial_db

    raw = json.loads(Path(results_path).read_text())
    meta = json.loads(Path(meta_path).read_text())
    info = raw.get("info", {})
    agent_model = (info.get("agent_info") or {}).get("llm") or ""
    user_model = (info.get("user_info") or {}).get("llm") or ""
    tasks = {str(t["id"]): Task.model_validate(t) for t in raw["tasks"]}
    by_role = {"assistant": AssistantMessage, "user": UserMessage, "tool": ToolMessage}
    rows = []
    for s in raw["simulations"]:
        tid = str(s["task_id"]); task = tasks[tid]; m = meta.get(tid, {})
        ri = s.get("reward_info") or {}
        err = ""
        try:
            L = ledger_for_run(task, s["messages"], m)
        except Exception as e:  # never silently $0
            L, err = None, f"ledger {type(e).__name__}: {e}"[:300]
        try:
            msgs = [by_role[x["role"]].model_validate(x) for x in s["messages"] if x.get("role") in by_role]
            g, a = gold_and_agent_dbs(task, msgs)
            dd = dollar_diff(g, a, initial_db(task))
            omission, dd_sev = dd.omission, dd.severity
        except Exception as e:
            omission = dd_sev = None; err += f" dd {type(e).__name__}: {e}"[:200]
        ta, tu = _usage(s["messages"], "assistant"), _usage(s["messages"], "user")
        ca, cu = cost_of(ta, agent_model), cost_of(tu, user_model)
        rows.append({
            "config": config_id, "sim": sim_label, "task_id": tid, "trial": s.get("trial"),
            "stratum": m.get("stratum"),
            "commission_usd": None if L is None else round(min(L.commission, BASIC_LIMIT), 2),
            "commission_uncapped_usd": None if L is None else round(L.commission, 2),
            "commission_event": None if L is None else L.event,
            "uncertain_usd": None if L is None else round(L.uncertain, 2),
            "ledger_kinds": "" if L is None else ";".join(sorted({i["kind"] for i in L.items})),
            "breach_kinds": "" if L is None else ";".join(sorted({i["kind"] for i in L.breaches})),
            "omission_usd": omission, "dd_severity_usd": dd_sev,
            "reward": ri.get("reward"), "db_match": (ri.get("db_check") or {}).get("db_match"),
            "failed": (ri.get("reward") != 1.0) or ((ri.get("db_check") or {}).get("db_match") is False),
            "termination": s.get("termination_reason"),
            "transferred": any(tc.get("name") == "transfer_to_human_agents" for x in s["messages"]
                               if x.get("role") == "assistant" for tc in (x.get("tool_calls") or [])),
            "agent_model": agent_model, "user_model": user_model,
            "cost_agent_usd": None if ca is None else round(ca, 6), "cost_user_usd": None if cu is None else round(cu, 6),
            "error": err.strip(),
        })
    return rows


def write_csv(rows, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    from loguru import logger
    logger.remove(); logger.add(sys.stderr, level="ERROR")
    rp = Path(sys.argv[1])
    rows = collect_runs(rp, sys.argv[2], sys.argv[3], sys.argv[4])
    hc, n, b = harness_cost(rp.parent / "harness.jsonl")
    write_csv(rows, sys.argv[5])
    tot = sum((r["cost_agent_usd"] or 0) + (r["cost_user_usd"] or 0) for r in rows) + hc
    print(json.dumps({"runs": len(rows), "errors": sum(bool(r["error"]) for r in rows), "cost_usd": round(tot, 4),
                      "harness_cost_usd": round(hc, 4), "harness_checks": n, "harness_blocks": b,
                      "unpriced": sum(r["cost_agent_usd"] is None or r["cost_user_usd"] is None for r in rows)}))
