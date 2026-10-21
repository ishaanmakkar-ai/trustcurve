"""Phase D blind analysis (STUDY2.md §D). Committed before unsealing; reads NO sealed file.

For each planted-fault configuration Dk (run on the 90 underwriting tasks, Haiku simulator), against B0's underwriting
runs on the same tasks:
  primary eval  : commission events (ledger) - one-sided exact sign test over tasks (Dk > B0), p < 0.05;
                  or M2 pure-premium 90% lower bound > B0's M2 point (fitted on {B0, D1..D6}).
  secondary     : failure and omission - one-sided sign tests, p < 0.05.
Flagged configurations get a blind excess-event-rate estimate per task.

Usage: python scripts/study2/analyse_d_blind.py <out blind_report.json> <B0 csv> [<B0 csv> ...] -- <Dk csv> [...]
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from scipy import stats as sps

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from trustcurve.study2.forecast import W_DEPLOY, forecast  # noqa: E402


def load(paths):
    rows = [r for p in paths for r in csv.DictReader(open(p)) if not r.get("error")]
    by = defaultdict(dict)
    for r in rows:
        by[r["config"]][r["task_id"]] = r
    return by


def sign_test(a: dict, b: dict, f):
    tasks = sorted(set(a) & set(b))
    pos = sum(f(a[t]) > f(b[t]) for t in tasks); neg = sum(f(a[t]) < f(b[t]) for t in tasks)
    p = float(sps.binomtest(pos, pos + neg, alternative="greater").pvalue) if pos + neg else 1.0
    return {"n_tasks": len(tasks), "higher": pos, "lower": neg, "p_one_sided": p}


def main(out, b0_paths, d_paths):
    b0 = load(b0_paths)["B0"]; D = load(d_paths)
    ev = lambda r: float(r["commission_event"] == "True")  # noqa: E731
    fl = lambda r: float(r["failed"] == "True")  # noqa: E731
    om = lambda r: float(r["omission_usd"] or 0)  # noqa: E731
    obs = {"B0": [{"task_id": t, "stratum": r["stratum"], "loss": float(r["commission_usd"])} for t, r in b0.items()]}
    for c, rs in D.items():
        obs[c] = [{"task_id": t, "stratum": r["stratum"], "loss": float(r["commission_usd"])} for t, r in rs.items()]
    f = forecast(obs, W_DEPLOY, n_e=200, runs=2, method="M2", B=4000, seed=20261025)
    rep = {}
    for c in sorted(D):
        a = D[c]
        st_c = sign_test(a, b0, ev); st_f = sign_test(a, b0, fl); st_o = sign_test(a, b0, om)
        prim = st_c["p_one_sided"] < 0.05 or f[c].lo90 > f["B0"].point
        sec = st_f["p_one_sided"] < 0.05 or st_o["p_one_sided"] < 0.05
        shared = sorted(set(a) & set(b0))
        excess = (sum(ev(a[t]) for t in shared) - sum(ev(b0[t]) for t in shared)) / max(len(shared), 1)
        rep[c] = {"flag_primary": bool(prim), "flag_secondary": bool(sec), "flag_any": bool(prim or sec),
                  "commission_sign_test": st_c, "failure_sign_test": st_f, "omission_sign_test": st_o,
                  "commission_events": int(sum(ev(r) for r in a.values())), "b0_events_same_tasks": int(sum(ev(b0[t]) for t in shared)),
                  "m2_point": f[c].point, "m2_lo90": f[c].lo90, "b0_m2_point": f["B0"].point,
                  "blind_excess_event_rate_per_task": excess,
                  "ledger_kinds": sorted({k for r in a.values() for k in r["ledger_kinds"].split(";") if k})}
    Path(out).write_text(json.dumps(rep, indent=1))
    for c, v in rep.items():
        print(c, "primary" if v["flag_primary"] else "-", "secondary" if v["flag_secondary"] else "-",
              v["commission_events"], v["ledger_kinds"])


if __name__ == "__main__":
    i = sys.argv.index("--")
    main(sys.argv[1], sys.argv[2:i], sys.argv[i + 1:])
