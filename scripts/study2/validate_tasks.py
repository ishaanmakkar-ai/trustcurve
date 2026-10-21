"""Validate a Study 2 task pool: schema, gold replay, metadata sidecar. No API calls.

Usage: python scripts/study2/validate_tasks.py <tasks.json> <meta.json> [--quiet]

Checks per task:
  1. tau2 Task schema validates;
  2. initial_state (if any) applies to the airline DB without error;
  3. every gold action executes without error, in order, on a fresh environment;
  4. the metadata sidecar has a valid entry (stratum, requester_user_id exists, etc.);
  5. ids are unique.
Prints one line per invalid task and a summary (counts per stratum, share whose gold moves money).
Exit code 1 if any task is invalid.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from copy import deepcopy

STRATA = {"cancel", "change", "book", "compensation", "other"}
REASONS = {"change_of_plan", "airline_cancelled", "health", "weather", "other", "none", "unknown"}
PRESSURE = {"none", "mild", "strong"}
REQUIRED = {"stratum", "requester_user_id", "correct_outcome", "gold_moves_money", "money_opportunity",
            "cancel_reason_category", "pressure", "incident_source", "boundary"}
MONEY_TOOLS = {"cancel_reservation", "send_certificate", "update_reservation_flights",
               "update_reservation_baggages", "book_reservation"}


def _payments(db):
    tot = 0.0
    for r in db["reservations"].values():
        tot += sum(float(p["amount"]) for p in r.get("payment_history", []))
    certs = sum(float(pm.get("amount", 0)) for u in db["users"].values()
                for pm in u.get("payment_methods", {}).values() if pm.get("source") == "certificate")
    return tot, certs


def check(task_raw, meta, env_ctor, Task):
    errs = []
    try:
        task = Task.model_validate(task_raw)
    except Exception as e:
        return [f"schema: {str(e)[:200]}"], None
    init = task.initial_state
    try:
        env = env_ctor()
        env.set_state(initialization_data=init.initialization_data if init else None,
                      initialization_actions=init.initialization_actions if init else None,
                      message_history=[], strict=True)
        db0 = env.tools.db.model_dump(mode="json")
    except Exception as e:
        return [f"initial_state: {str(e)[:200]}"], None
    for a in (task.evaluation_criteria.actions or []):
        try:
            env.make_tool_call(tool_name=a.name, requestor=a.requestor, **a.arguments)
        except Exception as e:
            errs.append(f"gold action {a.name} failed: {str(e)[:200]}")
    db1 = env.tools.db.model_dump(mode="json")
    m = meta.get(str(task.id))
    if m is None:
        errs.append("no metadata entry")
    else:
        miss = REQUIRED - set(m)
        if miss:
            errs.append(f"metadata missing {sorted(miss)}")
        if m.get("stratum") not in STRATA:
            errs.append(f"bad stratum {m.get('stratum')}")
        if m.get("cancel_reason_category") not in REASONS:
            errs.append(f"bad cancel_reason_category {m.get('cancel_reason_category')}")
        if m.get("pressure") not in PRESSURE:
            errs.append(f"bad pressure {m.get('pressure')}")
        if m.get("requester_user_id") not in db0["users"]:
            errs.append(f"requester_user_id {m.get('requester_user_id')} not in DB")
        p0, c0 = _payments(db0); p1, c1 = _payments(db1)
        moved = abs(p1 - p0) > 1e-6 or abs(c1 - c0) > 1e-6
        gold_tools = {a.name for a in (task.evaluation_criteria.actions or [])}
        if bool(m.get("gold_moves_money")) != (moved or bool(gold_tools & {"book_reservation", "cancel_reservation"})):
            errs.append(f"gold_moves_money={m.get('gold_moves_money')} but replay moved money={moved}")
    return errs, task


def main(tasks_path, meta_path, quiet=False):
    import tau2  # noqa: F401
    from loguru import logger
    logger.remove()
    from tau2.data_model.tasks import Task
    from tau2.registry import registry
    env_ctor = registry.get_env_constructor("airline")
    tasks = json.load(open(tasks_path)); meta = json.load(open(meta_path))
    if isinstance(meta, list):
        meta = {str(m["id"]): m for m in meta}
    ids = Counter(str(t.get("id")) for t in tasks)
    bad = 0; strata = Counter(); money = Counter(); incidents = 0
    for t in tasks:
        errs, _ = check(deepcopy(t), meta, env_ctor, Task)
        if ids[str(t.get("id"))] > 1:
            errs.append("duplicate id")
        if errs:
            bad += 1
            print(f"INVALID {t.get('id')}: " + " | ".join(errs))
        m = meta.get(str(t.get("id")), {})
        strata[m.get("stratum")] += 1
        money[(m.get("stratum"), bool(m.get("gold_moves_money")))] += 1
        incidents += bool(m.get("incident_source"))
    print(json.dumps({"tasks": len(tasks), "invalid": bad, "strata": dict(strata), "incident_derived": incidents,
                      "gold_moves_money_by_stratum": {f"{k[0]}|{k[1]}": v for k, v in sorted(money.items(), key=str)}},
                     indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], "--quiet" in sys.argv))
