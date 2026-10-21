"""Turn a tau2 results.json into one row per run with outcome, dollar loss, tokens and cost."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from trustcurve.dollar_diff import dollar_diff, gold_and_agent_dbs, initial_db
from trustcurve.policy import classify_items, insured_amounts

# Official Anthropic list prices, USD per million tokens (prompts <= 100K tokens).
# Source: Anthropic model price table (cached 2026-10-06). Prompts above 100K are priced
# at $0.50 / $2.50 for Haiku 5.5; the collector flags any call over that size.
PRICES = {"claude-haiku-5-5": (0.10, 0.50)}
LONG_PRICES = {"claude-haiku-5-5": (0.50, 2.50)}  # prompts > 100K tokens
LONG_PROMPT = 100_000
MONEY_TOOLS = {"cancel_reservation", "send_certificate", "update_reservation_flights",
               "update_reservation_baggages", "book_reservation"}


def request_type(task) -> str:
    """Stratum = what the customer asks for (review 1 #5), not what gold does."""
    instr = getattr(task.user_scenario, "instructions", None)
    text = " ".join(str(getattr(instr, k, "") or "") for k in ("reason_for_call", "task_instructions")).lower()
    for label, words in (("cancel", ("cancel",)),
                         ("book", ("book a", "book the", "new reservation", "want to book", "book one")),
                         ("change", ("change", "modify", "upgrade", "downgrade", "baggage", "bag", "passenger")),
                         ("compensation", ("compensat", "voucher", "delayed", "refund")),
                         ("info", ("how much", "check", "know"))):
        if any(w in text for w in words):
            return label
    return "other"


def _model_key(name: str) -> str:
    return name.split("/")[-1]


def _usage(messages, role):
    inp = out = calls = long_calls = long_in = long_out = 0
    for m in messages:
        if m.get("role") != role or not m.get("usage"):
            continue
        u = m["usage"]
        p, c = int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
        calls += 1
        if p > LONG_PROMPT:
            long_calls += 1; long_in += p; long_out += c
        else:
            inp += p; out += c
    return inp, out, calls, long_calls, long_in, long_out


def collect(results_path: Path) -> list[dict]:
    from tau2.data_model.message import AssistantMessage, ToolMessage, UserMessage
    from tau2.data_model.tasks import Task

    raw = json.loads(Path(results_path).read_text())
    info = raw.get("info", {})
    agent_model = _model_key(((info.get("agent_info") or {}).get("llm")) or "claude-haiku-5-5")
    user_model = _model_key(((info.get("user_info") or {}).get("llm")) or "claude-haiku-5-5")
    tasks = {str(t["id"]): Task.model_validate(t) for t in raw["tasks"]}
    by_role = {"assistant": AssistantMessage, "user": UserMessage, "tool": ToolMessage}

    rows = []
    for s in raw["simulations"]:
        task = tasks[str(s["task_id"])]
        msgs = [by_role[m["role"]].model_validate(m) for m in s["messages"] if m.get("role") in by_role]
        ri = s.get("reward_info") or {}
        bd = ri.get("reward_breakdown") or {}
        db_match = (ri.get("db_check") or {}).get("db_match")
        try:
            gold, agent = gold_and_agent_dbs(task, msgs)
            dd = dollar_diff(gold, agent, initial_db(task))
            pol = insured_amounts(classify_items(dd.items, agent))
            diff_error = ""
        except Exception as e:  # replay failure must be visible, never silently $0
            dd, pol, diff_error = None, None, f"{type(e).__name__}: {e}"[:300]
        a_in, a_out, a_calls, a_long, a_lin, a_lout = _usage(s["messages"], "assistant")
        u_in, u_out, u_calls, u_long, u_lin, u_lout = _usage(s["messages"], "user")
        try:
            pa, pu = PRICES[agent_model], PRICES[user_model]
            la, lu = LONG_PRICES[agent_model], LONG_PRICES[user_model]
            cost = (a_in * pa[0] + a_out * pa[1] + u_in * pu[0] + u_out * pu[1]
                    + a_lin * la[0] + a_lout * la[1] + u_lin * lu[0] + u_lout * lu[1]) / 1e6
        except KeyError:
            cost = None  # price unknown for this model: never guess
        gold_tools = {a.name for a in (task.evaluation_criteria.actions or [])}
        rows.append({
            "task_id": s["task_id"], "trial": s.get("trial"), "seed": s.get("seed"),
            "reward": ri.get("reward"), "db_reward": bd.get("DB"), "communicate_reward": bd.get("COMMUNICATE"),
            "db_match": db_match,
            "money_match": None if dd is None else dd.money_match,
            "loss_event": None if dd is None else dd.loss_event,
            "non_monetary_db_mismatch": None if dd is None else (db_match is False and dd.money_match),
            "payout_loss_usd": None if dd is None else dd.payout_loss,
            "customer_harm_usd": None if dd is None else dd.customer_harm,
            "severity_usd": None if dd is None else dd.severity,
            "omission_usd": None if dd is None else dd.omission,
            "wrongful_payout_usd": None if pol is None else pol["wrongful_payout"],
            "uncertain_payout_usd": None if pol is None else pol["uncertain_payout"],
            "permitted_divergence_usd": None if pol is None else pol["permitted_divergence"],
            "insured_loss_event": None if pol is None else (pol["wrongful_payout"] + pol["customer_harm"]) > 1e-6,
            "insured_loss_event_incl_uncertain": None if pol is None else (pol["wrongful_payout"] + pol["uncertain_payout"] + pol["customer_harm"]) > 1e-6,
            "loss_kinds": "" if dd is None else ";".join(sorted({i["kind"] for i in dd.items})),
            "diff_error": diff_error,
            "stratum": request_type(task),
            "gold_moves_money": bool(gold_tools & MONEY_TOOLS),
            "agent_in_tok": a_in, "agent_out_tok": a_out, "agent_calls": a_calls,
            "user_in_tok": u_in, "user_out_tok": u_out, "user_calls": u_calls,
            "long_prompt_calls": a_long + u_long,
            "cost_usd_from_tokens": None if cost is None else round(cost, 6),
            "cost_usd_tau2": round(sum(m.get("cost") or 0 for m in s["messages"]), 6),
            "duration_s": s.get("duration"), "termination": s.get("termination_reason"),
            "transferred": any(tc.get("name") == "transfer_to_human_agents" for m in s["messages"] if m.get("role") == "assistant" for tc in (m.get("tool_calls") or [])),
        })
    return rows


def write_csv(rows, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    from loguru import logger
    logger.remove(); logger.add(sys.stderr, level="ERROR")
    rows = collect(Path(sys.argv[1]))
    write_csv(rows, sys.argv[2])
    print(f"{len(rows)} runs -> {sys.argv[2]}")
