"""Compute the frozen phase-C forecasts from underwriting runs only (STUDY2.md §C).

Usage: python scripts/study2/make_forecasts.py <design.json> <out forecasts_frozen.json> <uw_runs.csv> [...]
design.json: {config: {"n_e": int, "group": "pre13" | "extended", "bridge_n": int}}

Primary method = M2 (phase-A loop 3). Review 7 #1 (winner's curse):
  * group "pre13" (the pre-registered configurations; K2 is scored on these): M2 fitted on these configurations
    only, using all their underwriting tasks;
  * group "extended" (added after screening): M2 fitted on these configurations only, using ONLY the second
    underwriting half (tasks/study2/underwriting/rest_ids.txt), i.e. never on the tasks that selected them.
Per configuration: combined (n_e x 2 runs, rho 0.5), single (n_e x 1, RQ5), bridge (bridge_n x 1, Haiku-simulator
bridge arm), m1c and m1 (secondaries), omission. Writes thinned predictive draws (1,000). Reads no experience data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from trustcurve.study2.forecast import W_DEPLOY, forecast  # noqa: E402

SEED, B, RHO, KEEP = 20261024, 4000, 0.5, 1000
REST = {l.strip() for l in (ROOT / "tasks/study2/underwriting/rest_ids.txt").read_text().split() if l.strip()}


def cluster_of(task_id: str) -> str:
    """Template clusters for M1c (review 6 #8): E3A/E3B/E3C templates; every other task is its own cluster."""
    t = str(task_id)
    return t[:3] if t.startswith("E3") else t


def fit_group(obs, omi, n_e, n_b, seed):
    out = {}
    comb = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M2", B=B, seed=seed)
    single = forecast(obs, W_DEPLOY, n_e=n_e, runs=1, rho=RHO, method="M2", B=B, seed=seed + 1)
    bridge = forecast(obs, W_DEPLOY, n_e=n_b, runs=1, rho=RHO, method="M2", B=B, seed=seed + 5)
    m1c = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M1c", B=B, seed=seed + 2)
    m1 = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M1", B=B, seed=seed + 4)
    om = forecast(omi, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M2", B=B, seed=seed + 3)
    for c in obs:
        out[c] = {"combined": comb[c].as_dict(KEEP), "single": single[c].as_dict(KEEP), "bridge": bridge[c].as_dict(KEEP),
                  "m1c": m1c[c].as_dict(KEEP), "m1": m1[c].as_dict(KEEP), "omission": om[c].as_dict(KEEP),
                  "underwriting_tasks": len({o["task_id"] for o in obs[c]})}
    return out


def main(design_path, out_path, run_paths):
    design = json.load(open(design_path))
    rows = [r for p in run_paths for r in csv.DictReader(open(p))]
    errors = [r for r in rows if r.get("error")]
    rows = [r for r in rows if not r.get("error") and r["config"] in design]
    configs, used = {}, 0
    for g in ("pre13", "extended"):
        members = [c for c, d in design.items() if d["group"] == g]
        if not members:
            continue
        obs, omi = defaultdict(list), defaultdict(list)
        for r in rows:
            if r["config"] not in members or (g == "extended" and r["task_id"] not in REST):
                continue
            obs[r["config"]].append({"task_id": r["task_id"], "stratum": r["stratum"],
                                     "loss": float(r["commission_usd"]), "cluster": cluster_of(r["task_id"])})
            omi[r["config"]].append({"task_id": r["task_id"], "stratum": r["stratum"],
                                     "loss": float(r["omission_usd"] or 0)})
            used += 1
        missing = [c for c in members if c not in obs]
        if missing:
            raise SystemExit(f"no underwriting runs for {missing}")
        res = fit_group(obs, omi, {c: int(design[c]["n_e"]) for c in members},
                        {c: max(int(design[c].get("bridge_n", 0)), 1) for c in members},
                        SEED + (0 if g == "pre13" else 100))
        for c in res:
            res[c]["group"] = g
        configs.update(res)
    out = {"meta": {"method_primary": "M2", "secondaries": ["M1c", "M1"], "seed": SEED, "B": B, "rho": RHO,
                    "W": W_DEPLOY, "design": design, "underwriting_runs_used": used,
                    "underwriting_run_errors_excluded": len(errors),
                    "extended_group_uses": "rest_ids.txt only (review 7 #1)",
                    "inputs_sha256": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in run_paths}},
           "configs": configs}
    Path(out_path).write_text(json.dumps(out, indent=1))
    print(hashlib.sha256(Path(out_path).read_bytes()).hexdigest())
    for c, v in configs.items():
        f = v["combined"]
        print(f"{c:8s} {v['group']:8s} n_u={f['n_tasks']:3d} events={f['n_events']:4.1f} point={f['point']:7.2f} "
              f"pred90[{f['pred_lo90']:6.2f},{f['pred_hi90']:6.2f}]")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
