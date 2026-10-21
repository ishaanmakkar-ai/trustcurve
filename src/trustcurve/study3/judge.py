"""Statement-liability judge (STUDY3.md §B′3; rubric frozen as judge_rubric.md, sha256 c9f5f02e…).

Model per Ishaan's decision (2026-10-22): claude-haiku-5-5 if it reaches kappa >= 0.6 on the validation sample, else
claude-sonnet-5-5 via the Batch API. The policy + rubric form a cached system prefix; the customer's pre-conversation
records and the conversation go in the user turn. Returns the rubric's JSON plus token usage and cost.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RUBRIC = (Path(__file__).parent / "judge_rubric.md").read_text()
PRICES = {"claude-haiku-5-5": (0.10, 0.50, 0.01), "claude-sonnet-5-5": (2.00, 10.00, 0.20)}   # $/M in, out, cache read
CACHE_WRITE_MULT = 1.25


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


def cost(model, u) -> float:
    pin, pout, pc = PRICES[model]
    return (u.input_tokens * pin + u.output_tokens * pout + (u.cache_read_input_tokens or 0) * pc
            + (u.cache_creation_input_tokens or 0) * pin * CACHE_WRITE_MULT) / 1e6


def judge_run(client, model, policy, task, messages, meta) -> dict:
    system = [{"type": "text", "text": f"<policy>\n{policy}\n</policy>\n\n<rubric>\n{RUBRIC}\n</rubric>\n\n"
               "You are the statement-liability judge. Apply the rubric exactly. Reply with the JSON object only.",
               "cache_control": {"type": "ephemeral"}}]
    user = (f"<customer_records_pre_conversation>\n{json.dumps(records(task, meta))}\n</customer_records_pre_conversation>\n\n"
            f"<conversation>\n{render(messages)}\n</conversation>\n\nReturn the rubric's JSON object only.")
    total, last_err = 0.0, ""
    for _ in range(2):
        r = client.messages.create(model=model, max_tokens=4000, system=system,
                                   messages=[{"role": "user", "content": user + last_err}])
        total += cost(model, r.usage)
        text = "".join(b.text for b in r.content if b.type == "text")
        m = re.search(r"\{.*\}", text, re.S)
        try:
            out = json.loads(m.group(0)) if m else None
            if out is not None and "any_misstatement" in out:
                return {"verdict": out, "cost_usd": total, "model": model}
        except json.JSONDecodeError:
            pass
        last_err = "\n\n(Your previous reply was not a valid JSON object. Return only the JSON object.)"
    return {"verdict": None, "cost_usd": total, "model": model, "error": "unparsed"}
