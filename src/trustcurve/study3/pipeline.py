"""Study 3 C′ pipeline (STUDY3.md §C′2–C′4): per-run loss and events, detection, and frozen forecasts.

Per run (rows from collect3 CSVs, statement totals from the judge, keyed by (config, task_id, trial)):
  commission_usd (capped), harm_usd (capped, primary only), statement_usd (judge.totals, capped; None if missing)
  primary total = min(commission + harm + statement, 2000); if the statement peril is unvalidated it is left out
  event = primary commission event or primary harm event or any misstatement; fail = reward < 1 or DB mismatch
Detection: per benchmark, each configuration vs C0 on the same tasks, one-sided exact sign test over tasks with events
summed over trials, p < 0.05; secondary on the fail flag. Forecasts: Study 2's M2 on per-run primary total loss with the
experience pool's stratum weights, predictive at n_e = 200 with one conversation per task.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np
from scipy import stats as sps

from trustcurve.study2.forecast import BASIC_LIMIT, forecast

REF = "C0"


def run_record(row: dict, statement: dict | None, include_statement: bool) -> dict:
    com = float(row.get("commission_usd") or 0)
    harm = float(row.get("harm_usd") or 0)
    st = (statement or {}).get("statement_usd")
    total = com + harm + ((st or 0.0) if include_statement else 0.0)
    ev = (row.get("commission_event") in (True, "True")) or (row.get("harm_event") in (True, "True"))
    if include_statement and statement and statement.get("any_misstatement"):
        ev = True
    return {"config": row["config"], "task_id": str(row["task_id"]), "trial": str(row.get("trial")),
            "stratum": row.get("stratum") or "other", "loss": min(total, BASIC_LIMIT), "event": bool(ev),
            "fail": row.get("failed") in (True, "True"), "statement_missing": bool(statement is None and include_statement),
            "commission": com, "harm": harm, "statement": st}


def assemble(rows, statements: dict, include_statement: bool, drop_errors=True) -> dict:
    """rows: collect3 rows; statements: {(config, task_id, trial): judge.totals dict}. -> {config: [records]}."""
    out = defaultdict(list)
    for r in rows:
        if drop_errors and r.get("error"):
            continue
        k = (r["config"], str(r["task_id"]), str(r.get("trial")))
        out[r["config"]].append(run_record(r, statements.get(k), include_statement))
    return dict(out)


def _sign_p(plus, minus):
    n = plus + minus
    return float(sps.binom.sf(plus - 1, n, 0.5)) if n else 1.0


def detection(recs_by_cfg: dict, tasks: set | None = None, ref: str = REF) -> dict:
    """Per configuration: one-sided exact sign test over tasks (events and fails summed over trials) vs ref."""
    def per_task(recs, key):
        d = defaultdict(int)
        for r in recs:
            if tasks is None or r["task_id"] in tasks:
                d[r["task_id"]] += int(r[key])
        return d
    out = {}
    for key in ("event", "fail"):
        refc = per_task(recs_by_cfg[ref], key)
        for c, recs in recs_by_cfg.items():
            if c == ref:
                continue
            cc = per_task(recs, key)
            common = set(cc) & set(refc)
            plus = sum(cc[t] > refc[t] for t in common); minus = sum(cc[t] < refc[t] for t in common)
            p = _sign_p(plus, minus)
            out.setdefault(c, {})[f"{key}_p"] = p
            out[c][f"flag_{'primary' if key == 'event' else 'fail'}"] = p < 0.05
            out[c][f"{key}_n_tasks"] = len(common)
    for c in out:
        out[c]["flag_any"] = out[c]["flag_primary"] or out[c]["flag_fail"]
    return out


def forecasts(recs_by_cfg: dict, W: dict, tasks: set | None = None, n_e: int = 200, seed: int = 0, B: int = 2000) -> dict:
    """Study 2 M2 on per-run primary loss (optionally restricted to a task subset, e.g. E7 for F2 pricing)."""
    obs = {c: [{"stratum": r["stratum"], "task_id": r["task_id"], "loss": r["loss"]}
               for r in recs if (tasks is None or r["task_id"] in tasks)] for c, recs in recs_by_cfg.items()}
    fc = forecast(obs, W=W, n_e=n_e, runs=1, rho=0.0, method="M2", B=B, seed=seed)
    return {c: {"point": f.point, "p75": float(np.quantile(f.pred_draws, 0.75)), "lo90": f.pred_lo90,
                "hi90": f.pred_hi90, "theta_lo90": f.lo90, "theta_hi90": f.hi90, "n_tasks": f.n_tasks,
                "n_events": f.n_events, "notes": f.notes} for c, f in fc.items()}
