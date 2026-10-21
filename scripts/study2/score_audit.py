"""Score a filled audit sheet against the sealed ledger key (Cohen's kappa on wrongful Y/N, dollar agreement,
disagreement list). Used for Ishaan's human audit and for the interim model second-rater.

Usage: python scripts/study2/score_audit.py <filled_sheet.csv> <out.json> [rater_label]
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY = ROOT / "study2_sealed" / "audit_key.json"


def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan"), po


def main(sheet, out, label="rater"):
    key = json.load(open(KEY))
    rows = {r["id"].strip(): r for r in csv.DictReader(open(sheet))}
    ycol = next(c for c in next(iter(rows.values())) if c.lower().startswith("wrongful"))
    ucol = next(c for c in next(iter(rows.values())) if "estimate" in c.lower())
    ids = sorted(i for i in key if i in rows and rows[i][ycol].strip().upper()[:1] in ("Y", "N"))
    a = [rows[i][ycol].strip().upper().startswith("Y") for i in ids]; b = [bool(key[i]["ledger_event"]) for i in ids]
    k, po = kappa(a, b)
    dis = [{"id": i, label: rows[i][ycol], "ledger_event": key[i]["ledger_event"], "ledger_usd": key[i]["ledger_commission_usd"],
            f"{label}_usd": rows[i][ucol], "ledger_kinds": key[i]["ledger_kinds"], "notes": rows[i].get("notes", "")[:300]}
           for i, x, y in zip(ids, a, b) if x != y]
    both = [i for i, x, y in zip(ids, a, b) if x and y]
    usd = []
    for i in both:
        try:
            usd.append((float(rows[i][ucol] or 0), float(key[i]["ledger_commission_usd"])))
        except ValueError:
            pass
    res = {"rater": label, "n_scored": len(ids), "kappa": k, "agreement": po,
           "rater_Y": sum(a), "ledger_Y": sum(b), "both_Y": len(both),
           "confusion": {"YY": sum(x and y for x, y in zip(a, b)), "YN": sum(x and not y for x, y in zip(a, b)),
                         "NY": sum((not x) and y for x, y in zip(a, b)), "NN": sum((not x) and not y for x, y in zip(a, b))},
           "dollar_pairs_both_Y": usd, "disagreements": dis}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k_: res[k_] for k_ in ("n_scored", "kappa", "agreement", "rater_Y", "ledger_Y", "confusion")}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "rater")
