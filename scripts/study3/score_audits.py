"""Score Ishaan's filled Study 3 audit sheets (STUDY3.md §B′3) once they are returned.

  statement : Cohen's kappa on any_misstatement, Ishaan vs the sealed judge output (study3_sealed/judge_validation/<model>.json);
              decides the judge per Ishaan's 2026-10-22 rule (Haiku if kappa >= 0.6, else Sonnet via batch).
  harm      : Cohen's kappa on customer_harmed, Ishaan vs ledger3 recomputed with the CURRENT rule (primary harm > 0).

Usage: python scripts/study3/score_audits.py statement <sheet.csv> <out.json> [judge_model]
       python scripts/study3/score_audits.py harm <sheet.csv> <out.json>
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts" / "study2"))
from score_audit import kappa  # noqa: E402


def yn(v):
    v = (v or "").strip().upper()[:1]
    return {"Y": True, "N": False}.get(v)


def main(kind, sheet, out, model="claude-haiku-5-5"):
    rows = {r["id"].strip(): r for r in csv.DictReader(open(sheet))}
    col = next(c for c in next(iter(rows.values())) if c.lower().startswith("misstatement" if kind == "statement" else "customer_harmed"))
    if kind == "statement":
        J = json.loads((ROOT / "study3_sealed" / "judge_validation" / f"{model}.json").read_text())
        auto = {a: bool((v.get("verdict") or {}).get("any_misstatement")) for a, v in J.items() if v.get("verdict")}
    else:
        from tau2.data_model.tasks import Task

        from trustcurve.study3.ledger3 import harm_for_run
        key = json.loads((ROOT / "study3_sealed" / "audit_keys" / "harm_key.json").read_text())
        meta = json.loads((ROOT / "tasks/study2/experience_main/meta.json").read_text())
        auto, cache = {}, {}
        for a, k in key.items():
            res = cache.setdefault(k["run"], json.loads((ROOT / "results/raw/study2" / k["run"] / "results.json").read_text()))
            s = next(x for x in res["simulations"] if str(x["task_id"]) == str(k["task_id"]) and x.get("trial") == k.get("trial"))
            t = Task.model_validate(next(x for x in res["tasks"] if str(x["id"]) == str(k["task_id"])))
            auto[a] = harm_for_run(t, s["messages"], meta.get(str(k["task_id"]), {})).event
    ids = sorted(i for i in auto if i in rows and yn(rows[i][col]) is not None)
    h, m = [yn(rows[i][col]) for i in ids], [auto[i] for i in ids]
    k, po = kappa(h, m)
    res = {"kind": kind, "model": model if kind == "statement" else "ledger3", "n": len(ids), "kappa": k, "agreement": po,
           "human_Y": sum(h), "auto_Y": sum(m),
           "disagreements": [{"id": i, "human": rows[i][col], "auto": a, "notes": rows[i].get("notes", "")[:200]}
                             for i, x, a in zip(ids, h, m) if x != a]}
    if kind == "statement":
        res["decision"] = ("use claude-haiku-5-5" if model == "claude-haiku-5-5" and k >= 0.6 else
                           "switch to claude-sonnet-5-5 via Batch API (re-run validation; $540 gate applies)" if model == "claude-haiku-5-5"
                           else ("statement peril validated" if k >= 0.6 else "statement peril unvalidated: excluded from totals"))
    Path(out).write_text(json.dumps(res, indent=1)); print(json.dumps({x: res[x] for x in res if x != "disagreements"}))


if __name__ == "__main__":
    main(*sys.argv[1:])
