"""Size the main run from pilot measurements (all targets in effective runs; see REVIEW.md #3)."""

from __future__ import annotations

import csv
import json
import math
import sys
from statistics import mean

from trustcurve.stats import Z90, icc_binary, group, wilson


def load(paths):
    rows = []
    for p in paths:
        rows += list(csv.DictReader(open(p)))
    return rows


def n_eff(n_runs: int, m: float, rho: float) -> float:
    return n_runs / (1 + (m - 1) * rho)


def effective_runs_needed(q: float, cv2: float, k: float) -> float:
    """Binomial limited-fluctuation pure-premium standard, in effective runs."""
    return (Z90 / k) ** 2 * ((1 - q) + cv2) / q


def tasks_needed(eff_runs: float, m: int, rho: float) -> float:
    return eff_runs * (1 + (m - 1) * rho) / m


def main(paths, n_tasks_available=50, cost_per_run=None, sec_per_run=None, conc=8):
    r = load(paths)
    tasks = sorted({x["task_id"] for x in r})
    n = len(r); m = n / len(tasks)
    fail = group(r, "task_id", lambda x: int(x["reward"] != "1.0"))
    rho_fail = icc_binary(fail)
    events = sum(x["insured_loss_event"] == "True" for x in r)
    events_u = sum(x["insured_loss_event_incl_uncertain"] == "True" for x in r)
    omis = sum(float(x["omission_usd"] or 0) > 0 for x in r)
    rho = max(rho_fail, 0.05)  # loss-event ICC is unestimable with 0 events; use failure ICC as proxy
    ne = n_eff(n, m, rho)
    q_hi = 1 - 0.05 ** (1 / ne) if events == 0 else wilson(events, round(ne))[1]
    cost = cost_per_run or mean(float(x["cost_usd_from_tokens"]) for x in r)
    sec = sec_per_run or mean(float(x["duration_s"]) for x in r)
    out = {
        "runs": n, "distinct_tasks": len(tasks), "mean_runs_per_task": round(m, 2),
        "benchmark_failures": sum(sum(v) for v in fail.values()),
        "failure_icc": round(rho_fail, 3), "effective_runs": round(ne, 1),
        "insured_loss_events": events, "insured_loss_events_incl_uncertain": events_u,
        "omission_runs": omis,
        "loss_rate_95_upper_one_sided": round(q_hi, 4),
        "cost_per_run_usd": round(cost, 4), "sec_per_run": round(sec, 1),
        "ceiling_effective_runs_50_tasks": round(n_tasks_available / rho, 1),
        "scenarios": [],
    }
    for q in (0.02, 0.05, 0.20):
        for cv2 in (1.0, 3.0):
            for k in (0.05, 0.10, 0.20):
                er = effective_runs_needed(q, cv2, k)
                tn2 = tasks_needed(er, 2, rho)
                out["scenarios"].append({
                    "q": q, "cv2": cv2, "k": k, "claims_equiv": round(er * q),
                    "effective_runs_needed": round(er), "feasible_with_50_tasks": er <= n_tasks_available / rho,
                    "distinct_tasks_needed_at_2_runs_each": math.ceil(tn2),
                    "runs_at_2_each": math.ceil(tn2) * 2,
                    "api_cost_usd": round(math.ceil(tn2) * 2 * cost, 2),
                    "wall_hours_at_conc": round(math.ceil(tn2) * 2 * sec / conc / 3600, 2),
                })
    a_runs = 50 * 20
    out["option_A_50x20"] = {"runs": a_runs, "api_cost_usd": round(a_runs * cost, 2),
                             "wall_hours_at_conc": round(a_runs * sec / conc / 3600, 2),
                             "effective_runs": round(n_eff(a_runs, 20, rho), 1)}
    return out


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1:]), indent=2))
