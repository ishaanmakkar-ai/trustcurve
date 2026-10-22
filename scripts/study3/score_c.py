"""Score C′ (STUDY3.md §C′6, S1) from the frozen forecasts and the experience runs. Reads no sealed file except the
experience-pool metadata (stratum/boundary_type for RQ5), which is legitimate after the F2 freeze.

Output: results/study3/phaseC/score_c.json (commit before running unseal_d.py).
Usage: python scripts/study3/score_c.py
"""

from __future__ import annotations

import csv
import glob
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from trustcurve.study3 import econ
    from trustcurve.study3.configs import CONFIGS3
    from trustcurve.study3.pipeline import assemble
    from trustcurve.study3.score import score_all
    R = ROOT / "results/study3"
    frozen = json.loads((R / "forecasts_frozen.json").read_text())
    rows = [r for f in sorted(glob.glob(str(R / "runs" / "exp-*.csv"))) for r in csv.DictReader(open(f))]
    model = frozen["judge_decision"]["model"]
    J = json.loads((R / "judge" / f"exp_{model}.json").read_text()) if (R / "judge" / f"exp_{model}.json").exists() else {}
    st = {tuple(k.split("|")): v["totals"] for k, v in J.items()}
    exp = assemble(rows, st, frozen["include_statement"])
    # RQ5: experience tasks whose (stratum, boundary_type) never appears among F2's trap tasks
    pool_meta = json.loads((ROOT / "tasks/study3_sealed/meta.json").read_text())
    f2_meta = json.loads((ROOT / "tasks/study3/F2/meta.json").read_text())
    covered = {(m.get("stratum"), m.get("boundary_type")) for t, m in f2_meta.items() if not t.startswith("E7-")}
    absent = {t for t, m in pool_meta.items() if (m.get("stratum"), m.get("boundary_type")) not in covered}
    exp_absent = {c: [r for r in recs if r["task_id"] in absent] for c, recs in exp.items()}
    out = score_all(frozen, exp, exp_absent)
    out["rq5_absent_tasks"] = len({r["task_id"] for recs in exp_absent.values() for r in recs})
    out["experience_runs"] = {c: len(v) for c, v in exp.items()}
    out["statement_missing"] = sum(r["statement_missing"] for recs in exp.values() for r in recs)
    # S1 economics on the frozen forecasts and per-conversation realised losses
    fcs = {f: frozen["forecasts"][f] for f in ("F1_3", "F1_1", "F2", "F3") if f in frozen["forecasts"]}
    losses = {c: np.array([r["loss"] for r in recs]) for c, recs in exp.items()}
    cards = {c: CONFIGS3[c].card for c in CONFIGS3}
    base_model = {c: CONFIGS3[c].model for c in CONFIGS3}
    clean = [c for c, v in CONFIGS3.items() if v.source == "clean"]
    out["econ"] = econ.run_all(fcs, losses, cards, base_model, clean)
    (R / "phaseC").mkdir(exist_ok=True)
    (R / "phaseC" / "score_c.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({"rq1": {k: out["rq1"][k] for k in ("H1", "H2", "H2_share", "H5", "did")},
                      "h3": out["h3"], "medlog": {f: v["medlog"] for f, v in out["pricing"].items()},
                      "kill_econ": out["econ"]["kill"]}, default=float))


if __name__ == "__main__":
    main()
