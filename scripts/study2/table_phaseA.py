"""Print the phase-A results table (markdown) from a grid JSON. Usage: python scripts/study2/table_phaseA.py <grid.json>"""

import json
import sys

g = json.load(open(sys.argv[1]))["grid"]
cols = ["cov_param", "cov_pred", "cov_up95", "relbias_mean", "relbias_median", "iscore_rel", "crps_rel",
        "pit_chi2_p", "pit_maxdev", "spear_median", "spear_p10", "conc_median"]
print("| cell | method | " + " | ".join(cols) + " | faulty / non-faulty cov |")
print("|" + "---|" * (len(cols) + 3))
for cell, d in g.items():
    for m in ("M1", "M2", "M2flat"):
        x = d[m]
        extra = f"{x['cov_pred_faulty']:.2f} / {x['cov_pred_nonfaulty']:.2f}" if "cov_pred_faulty" in x else ""
        vals = []
        for c in cols:
            v = x.get(c)
            vals.append("" if v is None else (f"{v:.3f}" if c == "pit_chi2_p" else f"{v:.2f}"))
        print(f"| {cell} | {m} | " + " | ".join(vals) + f" | {extra} |")
