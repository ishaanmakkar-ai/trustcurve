"""Realised commission $ by ledger kind in Study 2's committed run CSVs (anchor for Study 3 phase A' loop 3).

Usage: python scripts/study3/study2_loss_mix.py <out.json>
"""

from __future__ import annotations

import collections
import csv
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(out):
    res = {}
    for pre, name in (("exp-", "experience"), ("uw2-", "underwriting")):
        usd, ev, n = collections.Counter(), collections.Counter(), 0
        for f in sorted(glob.glob(str(ROOT / f"results/study2/runs/{pre}*.csv"))):
            for r in csv.DictReader(open(f)):
                if r.get("error"):
                    continue
                n += 1
                if r["commission_event"] == "True":
                    kinds = (r["ledger_kinds"] or "unknown").split(";")
                    for k in kinds:
                        usd[k] += float(r["commission_usd"]) / len(kinds); ev[k] += 1 / len(kinds)
        tot = sum(usd.values())
        res[name] = {"runs": n, "usd": round(tot, 2),
                     "by_kind": {k: {"usd": round(v, 2), "share": round(v / tot, 4), "events": round(ev[k], 1)}
                                 for k, v in usd.most_common()}}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
