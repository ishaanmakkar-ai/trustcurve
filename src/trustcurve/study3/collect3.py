"""Study 3 per-run collector: Study 2's commission row (collect2) plus the customer-harm peril (ledger3).

Statement liability is added later by the frozen judge (judge_rubric.md), as a separate pass.

Usage: python -m trustcurve.study3.collect3 <results.json> <meta.json> <config_id> <sim_label> <out.csv>
Prints the same JSON summary as collect2 (runs, errors, cost_usd, ...), plus harm totals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from trustcurve.study2.collect2 import collect_runs, harness_cost, write_csv
from trustcurve.study2.forecast import BASIC_LIMIT


def add_harm(rows, results_path, meta_path):
    from tau2.data_model.tasks import Task

    from trustcurve.study3.ledger3 import harm_for_run
    raw = json.loads(Path(results_path).read_text())
    meta = json.loads(Path(meta_path).read_text())
    tasks = {str(t["id"]): Task.model_validate(t) for t in raw["tasks"]}
    sims = {(str(s["task_id"]), s.get("trial")): s for s in raw["simulations"]}
    for r in rows:
        if r.get("error"):
            continue
        s = sims.get((r["task_id"], r["trial"]))
        try:
            H = harm_for_run(tasks[r["task_id"]], s["messages"], meta.get(r["task_id"], {}))
            r.update(harm_usd=round(min(H.harm, BASIC_LIMIT), 2), harm_uncapped_usd=round(H.harm, 2), harm_event=H.event,
                     harm_uncertain_usd=round(H.uncertain, 2),
                     harm_kinds=";".join(sorted({i["kind"] for i in H.items})))
        except Exception as e:  # never silently $0
            r["error"] = (r.get("error", "") + f" harm {type(e).__name__}: {e}")[:300].strip()
    return rows


if __name__ == "__main__":
    from loguru import logger
    logger.remove(); logger.add(sys.stderr, level="ERROR")
    rp = Path(sys.argv[1])
    rows = add_harm(collect_runs(rp, sys.argv[2], sys.argv[3], sys.argv[4]), rp, sys.argv[2])
    hc, n, b = harness_cost(rp.parent / "harness.jsonl")
    write_csv(rows, sys.argv[5])
    tot = sum((r.get("cost_agent_usd") or 0) + (r.get("cost_user_usd") or 0) for r in rows) + hc
    print(json.dumps({"runs": len(rows), "errors": sum(bool(r["error"]) for r in rows), "cost_usd": round(tot, 4),
                      "harness_cost_usd": round(hc, 4), "harness_checks": n,
                      "harm_events": sum(bool(r.get("harm_event")) for r in rows),
                      "commission_events": sum(bool(r.get("commission_event")) for r in rows)}))
