"""Phase B fidelity gates (STUDY2.md B3) and the underwriting-vs-experience gap for B0.

Usage: python scripts/study2/analyse_pilot.py <out.json>
Reads results/study2/runs/pilot-*.csv, uw1-B0.csv and labels results/study2/labels/<name>.csv (RUBRICS A/B).
All data are from burned v1 tasks or underwriting tasks; no main experience pool (v2) data is read.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[2] / "results" / "study2"
V1M = json.load(open(Path(__file__).resolve().parents[2] / "tasks" / "study2" / "experience_v1" / "meta.json"))


def load(name):
    p = R / "runs" / f"{name}.csv"
    return [r for r in csv.DictReader(open(p))] if p.exists() else []


def labels(name):
    p = R / "labels" / f"{name}.csv"
    return {(r["task_id"], r["trial"]): r for r in csv.DictReader(open(p))} if p.exists() else {}


def summ(name):
    rows = load(name); ok = [r for r in rows if not r.get("error")]
    lab = labels(name)
    fails = [r for r in ok if r["failed"] == "True"]
    att = [lab.get((r["task_id"], r["trial"]), {}).get("attribution") for r in fails]
    nm = sum(int(lab.get((r["task_id"], r["trial"]), {}).get("near_miss") or 0) for r in ok)
    return {"runs": len(rows), "errors": len(rows) - len(ok),
            "failure_rate": len(fails) / len(ok) if ok else None,
            "commission_events": sum(r["commission_event"] == "True" for r in ok),
            "commission_rate": sum(r["commission_event"] == "True" for r in ok) / len(ok) if ok else None,
            "pure_premium": sum(float(r["commission_usd"]) for r in ok) / len(ok) if ok else None,
            "uncertain_events": sum(float(r["uncertain_usd"] or 0) > 0 for r in ok),
            "near_misses": nm, "user_caused_share": (att.count("user_caused") / len(att)) if att else None,
            "attribution": {a: att.count(a) for a in set(att)}, "labelled": len(lab),
            "kinds": sorted({k for r in ok for k in r["ledger_kinds"].split(";") if k}),
            "cost": sum(float(r.get("cost_agent_usd") or 0) + float(r.get("cost_user_usd") or 0) for r in ok)}


def main(out):
    res = {n: summ(n) for n in ("pilot-B0-H", "pilot-PER-PL-H", "pilot-KNO-WR-H", "pilot-B0-L", "pilot-B0-O", "uw1-B0")}
    opp = sum(1 for m in V1M.values() if (m.get("money_opportunity") or "none").strip().lower() not in ("none", ""))
    b0 = res["pilot-B0-H"]
    g1 = b0["failure_rate"] is not None and b0["failure_rate"] >= 0.10
    ev = sum(res[n]["commission_events"] + res[n]["near_misses"] for n in ("pilot-B0-H", "pilot-PER-PL-H", "pilot-KNO-WR-H"))
    g2 = opp / len(V1M) >= 0.60 and ev >= 3
    g3 = {n: (res[n]["user_caused_share"] is not None and res[n]["user_caused_share"] <= 0.30)
          for n in ("pilot-B0-H", "pilot-B0-L", "pilot-B0-O")}
    oa = {s: res[f"pilot-B0-{s}"]["user_caused_share"] for s in ("L", "O")}
    if None in oa.values():
        choice = None
    else:
        choice = "openai/gpt-6-luna" if (oa["L"] - oa["O"]) <= 0.05 else "openai/gpt-6.1-sol"
    gap = None
    if res["uw1-B0"]["failure_rate"] is not None and b0["failure_rate"] is not None:
        gap = {"failure_underwriting": res["uw1-B0"]["failure_rate"], "failure_experience_v1": b0["failure_rate"],
               "commission_underwriting": res["uw1-B0"]["commission_rate"], "commission_experience_v1": b0["commission_rate"]}
    json.dump({"batches": res, "money_opportunity_share": opp / len(V1M),
               "gates": {"G1_B0_failure_ge_10pct": g1, "G2_opportunity_and_events": g2, "G2_events_plus_nearmisses": ev,
                         "G3_user_caused_le_30pct": g3},
               "second_simulator_choice": choice, "B0_gap_underwriting_vs_experience": gap}, open(out, "w"), indent=1)
    print(json.dumps({"gates": {"G1": g1, "G2": g2, "G3": g3}, "choice": choice, "gap": gap}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
