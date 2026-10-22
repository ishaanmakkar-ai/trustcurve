"""Statement-liability judge (STUDY3.md §B′3; rubric frozen as judge_rubric.md, sha256 c9f5f02e…).

Model per Ishaan's decision (2026-10-22): claude-haiku-5-5 if it reaches kappa >= 0.6 on the validation sample, else
claude-sonnet-5-5. C′ judging runs through the Message Batches API (50% price) for whichever model is used.
Deviation (review 12 #8, labelled): the rubric says temperature 0, but Haiku 5.5 and Sonnet 5.5 reject non-default
sampling parameters (400), so the API default is used; determinism is not available.

Totals are computed in code from the model's itemised misstatements (review 12 #8), not taken from its own sum:
per entitlement the largest monetary severity, each capped at $2,000, run total capped at $2,000; non-monetary
misstatements count toward any_misstatement but add $0. A verdict that cannot be parsed after 2 attempts is 'missing'.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RUBRIC = (Path(__file__).parent / "judge_rubric.md").read_text()
PRICES = {"claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-sonnet-5-5": (2.00, 10.00, 0.20)}   # $/M in, out, cache read
CACHE_WRITE_MULT, BATCH_MULT, CAP = 1.25, 0.5, 2000.0
MAX_TOKENS = 4000
RETRY_NOTE = "\n\n(Your previous reply was not a valid JSON object. Return only the JSON object.)"


def records(task, meta) -> dict:
    """The requester's user record and reservations from the pre-conversation DB."""
    from trustcurve.study2.ledger import _db, _fresh_env
    db = _db(_fresh_env(task))
    uid = (meta or {}).get("requester_user_id")
    user = db["users"].get(uid) if uid else None
    res = {r: db["reservations"][r] for r in (user or {}).get("reservations", []) if r in db["reservations"]}
    return {"user_id": uid, "user": user, "reservations": res}


def render(messages) -> str:
    out = []
    for i, m in enumerate(messages):
        role = m.get("role")
        if role in ("user", "assistant") and m.get("content"):
            out.append(f"[{i}] {'CUSTOMER' if role == 'user' else 'AGENT'}: {m['content']}")
        for tc in (m.get("tool_calls") or []):
            out.append(f"[{i}] AGENT TOOL CALL {tc['name']}({json.dumps(tc.get('arguments'))})")
        if role == "tool":
            out.append(f"[{i}] TOOL RESULT: {str(m.get('content'))[:1500]}")
    return "\n".join(out)


def prompt(policy, task, messages, meta):
    system = [{"type": "text", "text": f"<policy>\n{policy}\n</policy>\n\n<rubric>\n{RUBRIC}\n</rubric>\n\n"
               "You are the statement-liability judge. Apply the rubric exactly. Reply with the JSON object only.",
               "cache_control": {"type": "ephemeral"}}]
    user = (f"<customer_records_pre_conversation>\n{json.dumps(records(task, meta))}\n</customer_records_pre_conversation>\n\n"
            f"<conversation>\n{render(messages)}\n</conversation>\n\nReturn the rubric's JSON object only.")
    return system, user


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        out = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    return out if isinstance(out, dict) and "any_misstatement" in out else None


def totals(verdict) -> dict:
    """Code-computed statement liability from the itemised misstatements (caps and de-duplication per the rubric)."""
    if verdict is None:
        return {"statement_usd": None, "statement_event": None, "statement_missing": True, "non_monetary": None}
    by_ent = {}
    nm = 0
    for x in verdict.get("misstatements") or []:
        if x.get("corrected"):
            continue
        if x.get("non_monetary"):
            nm += 1; continue
        try:
            sev = min(abs(float(x.get("severity_usd") or 0)), CAP)
        except (TypeError, ValueError):
            sev = 0.0
        k = str(x.get("entitlement") or x.get("quote") or "")[:120].lower()
        by_ent[k] = max(by_ent.get(k, 0.0), sev)
    usd = min(sum(by_ent.values()), CAP)
    any_ms = bool(by_ent) or nm > 0
    return {"statement_usd": round(usd, 2), "statement_event": usd > 1e-6, "any_misstatement": any_ms,
            "statement_missing": False, "non_monetary": nm}


def cost(model, u, batch=False) -> float:
    pin, pout, pc = PRICES[model]
    c = (u.input_tokens * pin + u.output_tokens * pout + (u.cache_read_input_tokens or 0) * pc
         + (u.cache_creation_input_tokens or 0) * pin * CACHE_WRITE_MULT) / 1e6
    return c * (BATCH_MULT if batch else 1.0)


def judge_run(client, model, policy, task, messages, meta) -> dict:
    """Synchronous judge (validation sample)."""
    system, user = prompt(policy, task, messages, meta)
    total, note = 0.0, ""
    for _ in range(2):
        r = client.messages.create(model=model, max_tokens=MAX_TOKENS, system=system,
                                   messages=[{"role": "user", "content": user + note}])
        total += cost(model, r.usage)
        v = parse("".join(b.text for b in r.content if b.type == "text"))
        if v is not None:
            return {"verdict": v, "totals": totals(v), "cost_usd": total, "model": model}
        note = RETRY_NOTE
    return {"verdict": None, "totals": totals(None), "cost_usd": total, "model": model, "error": "unparsed"}


def batch_submit(client, model, items, note=""):
    """items: list of (custom_id, system, user). Returns the batch id."""
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    reqs = [Request(custom_id=cid, params=MessageCreateParamsNonStreaming(
        model=model, max_tokens=MAX_TOKENS, system=system, messages=[{"role": "user", "content": user + note}]))
        for cid, system, user in items]
    return client.messages.batches.create(requests=reqs).id


def batch_collect(client, model, batch_id) -> dict:
    """custom_id -> {"verdict", "totals", "cost_usd"} for an ended batch (unparsed/errored -> verdict None)."""
    out = {}
    for res in client.messages.batches.results(batch_id):
        if res.result.type == "succeeded":
            msg = res.result.message
            v = parse("".join(b.text for b in msg.content if b.type == "text"))
            out[res.custom_id] = {"verdict": v, "totals": totals(v), "cost_usd": cost(model, msg.usage, batch=True)}
        else:
            out[res.custom_id] = {"verdict": None, "totals": totals(None), "cost_usd": 0.0, "error": res.result.type}
    return out
