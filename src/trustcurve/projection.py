"""Size the main run from pilot measurements (review 3 corrections).

* Target population must be stated. Two framings are reported:
  (a) the 50 τ²-bench airline tasks themselves (finite set; repetition converges, no ceiling);
  (b) a large pool of tasks of which the 50 are treated as a random sample (ceiling N/rho).
  Neither is the insured's real traffic; that gap is bias, not precision (PILOT.md).
* rho is the ICC of the DB-mismatch indicator (loss-relevant), reported with a cluster bootstrap
  interval; the reward-failure ICC is shown for comparison only.
* The robust zero-event bound treats tasks as the units (worst case over any heterogeneity).
* Estimates use the breadth batch (random tasks) only; pooled numbers are shown for reference.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from statistics import mean

from trustcurve.stats import (Z90, group, icc_binary, icc_bootstrap, weighted_cluster_size,
                              zero_event_upper)


def load(paths):
    rows = []
    for p in paths:
        rows += list(csv.DictReader(open(p)))
    return rows


def eff_runs_needed(q, cv2, k, z=Z90):
    return (z / k) ** 2 * ((1 - q) + cv2) / q


def summarize(rows):
    cl_db = group(rows, "task_id", lambda x: int(x["db_match"] != "True"))
    cl_fail = group(rows, "task_id", lambda x: int(x["reward"] != "1.0"))
    sizes = [len(v) for v in cl_db.values()]
    n, T = len(rows), len(cl_db)
    rho_db, rho_fail = icc_binary(cl_db), icc_binary(cl_fail)
    med, lo, hi = icc_bootstrap(cl_db)
    mw = weighted_cluster_size(sizes)
    events = sum(x["insured_loss_event"] == "True" for x in rows)
    neff = n / (1 + (mw - 1) * max(rho_db, 0.0))
    return {
        "runs": n, "distinct_tasks": T, "weighted_cluster_size": round(mw, 3),
        "insured_loss_events": events,
        "icc_db_mismatch": round(rho_db, 3), "icc_db_mismatch_boot95": [round(lo, 3), round(hi, 3)],
        "icc_reward_failure_for_comparison": round(rho_fail, 3),
        "effective_runs": round(neff, 1),
        "upper95_independent_runs": round(zero_event_upper(n), 4) if events == 0 else None,
        "upper95_effective_runs": round(zero_event_upper(neff), 4) if events == 0 else None,
        "upper95_robust_tasks_as_units": round(zero_event_upper(T), 4) if events == 0 else None,
        "cost_per_run_usd": round(mean(float(x["cost_usd_from_tokens"]) for x in rows), 4),
        "user_sim_cost_share": round(sum((int(x["user_in_tok"]) * 0.10 + int(x["user_out_tok"]) * 0.50) / 1e6 for x in rows)
                                     / sum(float(x["cost_usd_from_tokens"]) for x in rows), 3),
        "sec_per_run_mean": round(mean(float(x["duration_s"]) for x in rows), 1),
    }


def main(breadth_path, pilot_path=None, n_tasks=50):
    b = load([breadth_path]); s = summarize(b)
    out = {"estimand_note": "Rates are for the τ²-bench airline task distribution under this rating cell, "
                            "not an insured's real traffic (bias not addressed by these numbers).",
           "breadth_only": s}
    if pilot_path:
        out["pooled_reference"] = summarize(load([pilot_path, breadth_path]))
    rho_lo, rho, rho_hi = max(s["icc_db_mismatch_boot95"][0], 0.01), max(s["icc_db_mismatch"], 0.01), s["icc_db_mismatch_boot95"][1]
    out["framing_a_finite_50_tasks"] = {
        "note": "Target = the 50 tasks themselves: no ceiling; with 0 events, bound -> 1-0.05^(1/runs).",
        "option_A_50x20_upper95_if_0_events": round(zero_event_upper(1000), 4)}
    scen = []
    for q in (0.02, 0.05, 0.08, 0.20):
        for cv2, label in ((0.0, "frequency only"), (1.0, "pure premium CV2=1"), (3.0, "pure premium CV2=3")):
            for k in (0.10, 0.20):
                er = eff_runs_needed(q, cv2, k)
                scen.append({"q": q, "cv2": cv2, "standard": label, "k": k,
                             "effective_runs_needed": round(er),
                             "ceiling_50_tasks_at_rho_[lo,point,hi]": [round(n_tasks / r) for r in (rho_lo, rho, rho_hi)],
                             "feasible_with_50_tasks_at_point_rho": er <= n_tasks / rho,
                             "max_rho_for_50_tasks": round(n_tasks / er, 4),
                             "min_distinct_tasks_at_point_rho": math.ceil(rho * er),
                             "tasks_at_2_runs_each": math.ceil(er * (1 + rho) / 2)})
    out["framing_b_large_task_pool"] = {
        "note": "Tasks treated as a random sample from a large pool. Variants nested in a parent task are NOT "
                "independent new tasks: effective n is capped near P/rho_parent (unmeasured).",
        "rho_used_[lo,point,hi]": [rho_lo, rho, rho_hi], "scenarios": scen}
    c = s["cost_per_run_usd"]
    out["costs"] = {"api_per_run_haiku_user_sim": c,
                    "api_per_run_sonnet_user_sim_est": round(c * ((1 - s["user_sim_cost_share"]) + s["user_sim_cost_share"] * 20), 4),
                    "note": "Excludes judge (~1%) and the cost of generating and validating new tasks, "
                            "which dominates option B. Sonnet 5.5 is 20x Haiku per token."}
    return out


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), indent=2))
