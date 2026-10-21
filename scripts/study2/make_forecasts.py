"""Compute the frozen phase-C forecasts from underwriting runs only (STUDY2.md §C).

Usage: python scripts/study2/make_forecasts.py <design.json> <out forecasts_frozen.json> <uw_runs.csv> [...]
design.json: {config: [n_u, n_e]}  (n_e = experience tasks per simulator for that configuration)

Primary method = M2 (phase-A loop 3 fallback decision, STUDY2.md A3). For each configuration: combined (M2, n_e x 2
runs, rho 0.5), single (M2, n_e x 1 run), m1c and m1 (secondaries, n_e x 2), omission (M2 on omission loss). Writes thinned predictive draws (1,000) so the scorer can compute CRPS/PIT.
Reads no experience data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from trustcurve.study2.forecast import W_DEPLOY, forecast  # noqa: E402

SEED, B, RHO, KEEP = 20261024, 4000, 0.5, 1000


def cluster_of(task_id: str) -> str:
    """Template clusters for M1c (review 6 #8): E3A/E3B/E3C templates; every other task is its own cluster."""
    t = str(task_id)
    return t[:3] if t.startswith("E3") else t


def main(design_path, out_path, run_paths):
    design = json.load(open(design_path))
    rows = [r for p in run_paths for r in csv.DictReader(open(p))]
    errors = [r for r in rows if r.get("error")]
    rows = [r for r in rows if not r.get("error") and r["config"] in design]
    obs, omi = defaultdict(list), defaultdict(list)
    for r in rows:
        obs[r["config"]].append({"task_id": r["task_id"], "stratum": r["stratum"], "loss": float(r["commission_usd"]),
                                 "cluster": cluster_of(r["task_id"])})
        omi[r["config"]].append({"task_id": r["task_id"], "stratum": r["stratum"],
                                 "loss": float(r["omission_usd"] or 0)})
    missing = [c for c in design if c not in obs]
    if missing:
        raise SystemExit(f"no underwriting runs for {missing}")
    n_e = {c: int(v[1]) for c, v in design.items()}
    comb = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M2", B=B, seed=SEED)
    single = forecast(obs, W_DEPLOY, n_e=n_e, runs=1, rho=RHO, method="M2", B=B, seed=SEED + 1)
    m1c = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M1c", B=B, seed=SEED + 2)
    m1 = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M1", B=B, seed=SEED + 4)
    om = forecast(omi, W_DEPLOY, n_e=n_e, runs=2, rho=RHO, method="M2", B=B, seed=SEED + 3)
    out = {"meta": {"method_primary": "M2", "secondaries": ["M1c", "M1"], "seed": SEED, "B": B, "rho": RHO, "W": W_DEPLOY, "design": design,
                    "underwriting_runs": len(rows), "underwriting_run_errors_excluded": len(errors),
                    "inputs_sha256": {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in run_paths}},
           "configs": {c: {"combined": comb[c].as_dict(KEEP), "single": single[c].as_dict(KEEP),
                           "m1c": m1c[c].as_dict(KEEP), "m1": m1[c].as_dict(KEEP),
                           "omission": om[c].as_dict(KEEP),
                           "underwriting_tasks": len({o["task_id"] for o in obs[c]})} for c in design}}
    Path(out_path).write_text(json.dumps(out, indent=1))
    print(hashlib.sha256(Path(out_path).read_bytes()).hexdigest())
    for c in design:
        f = comb[c]
        print(f"{c:8s} n_u={f.n_tasks:3d} events={f.n_events:4.1f} point={f.point:7.2f} "
              f"90%[{f.lo90:6.2f},{f.hi90:6.2f}] pred[{f.pred_lo90:6.2f},{f.pred_hi90:6.2f}]")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
