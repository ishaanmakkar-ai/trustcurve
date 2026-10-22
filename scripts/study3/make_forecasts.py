"""Freeze every Study 3 forecast before the experience period (STUDY3.md §C′3–C′4).

Inputs: underwriting runs results/study3/runs/uw-F1-*.csv and uw-F2-*.csv; judge totals results/study3/judge/uw_<model>.json;
the statement decision results/study3/judge_decision.json ({"include_statement": bool, "model": ...}; absent -> the
statement peril is unvalidated and excluded from the primary total); W from results/study3/W_deploy.json; E7 ids from
the frozen F2 meta; cards from configs; optional underwriter prices results/study3/f3_prices.csv (+ sealed card map).
Output: results/study3/forecasts_frozen.json (commit it, with the printed SHA-256 in the message, before any experience run).

Usage: python scripts/study3/make_forecasts.py
"""

from __future__ import annotations

import csv
import glob
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from trustcurve.study3.configs import CONFIGS3
    from trustcurve.study3.pipeline import freeze_all
    R = ROOT / "results/study3"
    rows = lambda pat: [r for f in sorted(glob.glob(str(R / "runs" / pat))) for r in csv.DictReader(open(f))]
    f1_rows, f2_rows = rows("uw-F1-*.csv"), rows("uw-F2-*.csv")
    assert f1_rows and f2_rows, "underwriting runs missing"
    dec_p = R / "judge_decision.json"
    dec = json.loads(dec_p.read_text()) if dec_p.exists() else {"include_statement": False, "model": "claude-haiku-5-5",
                                                                "note": "no human labels yet: statement peril unvalidated"}
    jp = R / "judge" / f"uw_{dec['model']}.json"
    J = json.loads(jp.read_text()) if jp.exists() else {}
    statements = {tuple(k.split("|")): v["totals"] for k, v in J.items()}
    W = json.loads((R / "W_deploy.json").read_text())
    e7 = {t for t in json.loads((ROOT / "tasks/study3/F2/meta.json").read_text()) if t.startswith("E7-")}
    cards = {c: CONFIGS3[c].card for c in CONFIGS3}
    f3_rows, card_map = None, None
    if (R / "f3_prices.csv").exists():
        f3_rows = list(csv.DictReader(open(R / "f3_prices.csv")))
        card_map = json.loads((ROOT / "study3_sealed/card_map.json").read_text())["mapping"]
    out = freeze_all(f1_rows, f2_rows, statements, bool(dec["include_statement"]), W, e7, cards, f3_rows, card_map)
    out["judge_decision"] = dec
    out["judge_coverage"] = {"judged_runs": len(statements), "uw_runs": len(f1_rows) + len(f2_rows)}
    b = json.dumps(out, indent=1, sort_keys=True, default=float).encode()
    (R / "forecasts_frozen.json").write_bytes(b)
    print(json.dumps({"sha256": hashlib.sha256(b).hexdigest(), "forecasters": sorted(out["forecasts"]),
                      "include_statement": out["include_statement"], "judge_coverage": out["judge_coverage"]}))


if __name__ == "__main__":
    main()
