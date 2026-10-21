"""Phase A loop-3 figure (real underwriting pool): predictive coverage and upper-95 coverage by scenario and method.
Usage: python scripts/study2/fig_phaseA3.py results/study2/phaseA/grid_loop3.json results/study2/phaseA/
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERIES = {"M1": "#2a78d6", "M1c": "#1baf7a", "M2": "#eb6834"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SCEN = ["R0", "R2", "R6", "R5"]
LAB = {"R0": "R0 real pool", "R2": "R2 symmetric shift", "R6": "R6 harder experience", "R5": "R5 rare"}

g = json.load(open(sys.argv[1]))["grid"]; out = Path(sys.argv[2])
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, metric, title in ((axes[0], "cov_pred", "90% predictive coverage"), (axes[1], "cov_up95", "upper-95 coverage")):
    w = 0.26
    for i, m in enumerate(SERIES):
        ys = [g[f"{s}|nu=90|ne=200"][m][metric] for s in SCEN]
        ax.bar([j + (i - 1) * w for j in range(len(SCEN))], ys, width=w - 0.03, color=SERIES[m], label=m)
    ax.axhline(0.90 if metric == "cov_pred" else 0.95, color=INK2, linestyle="--", linewidth=1)
    ax.axhline(0.80, color="#e34948", linestyle=":", linewidth=1)
    ax.set_xticks(range(len(SCEN))); ax.set_xticklabels([LAB[s] for s in SCEN], fontsize=8.5)
    ax.set_title(f"{title} (n_u = 90, n_e = 200)", loc="left", fontsize=10.5, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK2, labelsize=8.5); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True); ax.set_ylim(0, 1)
axes[0].legend(frameon=False, fontsize=8.5, loc="lower left")
fig.suptitle("Phase A loop 3: known-truth simulation with the real underwriting pool (dashed: nominal; dotted: K1 line)",
             fontsize=9, color=INK2, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(out / "coverage_loop3.png", dpi=150)
print("figure ->", out / "coverage_loop3.png")
