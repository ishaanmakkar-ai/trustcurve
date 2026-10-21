"""B′ fidelity-pilot gates (STUDY3.md §"B′ fidelity pilot"): G1 failure rate, G-trunc confirm-and-stop cut-offs, and
the inputs for G3 (user_caused share of failures, from the RUBRICS labeller CSV if present).

G-trunc: the conversation's last talk message is the customer's and contains ###STOP###, and the agent executed fewer
of the gold's state-changing actions than the gold (the agent never got to act on a confirmed request).

Usage: python scripts/study3/pilot_gates.py <batch_name> [<batch_name> ...]
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRITES = {"cancel_reservation", "send_certificate", "update_reservation_flights", "update_reservation_baggages",
          "book_reservation", "update_reservation_passengers"}


def gates(name):
    rows = list(csv.DictReader(open(ROOT / "results/study3/runs" / f"{name}.csv")))
    R = json.loads((ROOT / "results/raw/study3" / name / "results.json").read_text())
    sims = {(str(s["task_id"]), str(s.get("trial"))): s for s in R["simulations"]}
    tasks = {str(t["id"]): t for t in R["tasks"]}
    ok = [r for r in rows if not r.get("error")]
    fails = [r for r in ok if r["failed"] == "True"]
    cut = 0
    for r in ok:
        s = sims[(r["task_id"], str(r["trial"]))]
        talk = [m for m in s["messages"] if m["role"] in ("user", "assistant") and (m.get("content") or m.get("tool_calls"))]
        gold = [a["name"] for a in (tasks[r["task_id"]]["evaluation_criteria"].get("actions") or []) if a["name"] in WRITES]
        done = [tc["name"] for m in s["messages"] if m["role"] == "assistant" for tc in (m.get("tool_calls") or []) if tc["name"] in WRITES]
        if talk and talk[-1]["role"] == "user" and "###STOP###" in (talk[-1].get("content") or "") and len(done) < len(gold):
            cut += 1
    lab = ROOT / "study3_sealed/labels" / f"{name}.csv"
    uc = None
    if lab.exists():
        L = {(x["task_id"], x.get("trial")): x for x in csv.DictReader(open(lab))}
        fl = [L.get((r["task_id"], r["trial"])) for r in fails]
        fl = [x for x in fl if x]
        uc = (sum(x.get("attribution") == "user_caused" for x in fl), len(fl))
    return {"batch": name, "runs": len(ok), "errors": len(rows) - len(ok), "G1_failure_rate": round(len(fails) / max(len(ok), 1), 4),
            "failures": len(fails), "G_trunc_rate": round(cut / max(len(ok), 1), 4), "cutoffs": cut,
            "G3_user_caused_of_failures": uc}


if __name__ == "__main__":
    out = [gates(n) for n in sys.argv[1:]]
    print(json.dumps(out, indent=1))
    p = ROOT / "results/study3/phaseB/pilot_gates.json"; p.write_text(json.dumps(out, indent=1))
