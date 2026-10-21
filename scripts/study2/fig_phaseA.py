"""Phase A figures from the committed grid JSON (regenerates exactly).

Usage: python scripts/study2/fig_phaseA.py results/study2/phaseA/<grid>.json results/study2/phaseA/
Outputs: coverage.png (predictive coverage by scenario x method at n_e=200), spearman.png, pit_S0.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERIES = {"M1": "#2a78d6", "M2": "#eb6834", "M2flat": "#1baf7a"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SCEN = ["S0", "S1", "S2", "S3", "S4", "S5"]
SCEN_LABEL = {"S0": "S0 well-specified", "S1": "S1 wrong mix", "S2": "S2 author shift", "S3": "S3 simulator shift",
              "S4": "S4 unseen fault", "S5": "S5 rare events"}


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)


def main(grid_path, out_dir):
    g = json.load(open(grid_path))["grid"]; out = Path(out_dir)
    for metric, fname, ylab, ref in (("cov_pred", "coverage.png", "90% predictive coverage", (0.90, 0.80)),
                                    ("spear_median", "spearman.png", "median Spearman (forecast vs realised)", (0.7, 0.3))):
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
        for ax, nu in zip(axes, (45, 90, 180)):
            w = 0.26
            for i, m in enumerate(SERIES):
                ys = [g[f"{s}|nu={nu}|ne=200"][m][metric] for s in SCEN]
                xs = [j + (i - 1) * w for j in range(len(SCEN))]
                ax.bar(xs, ys, width=w - 0.03, color=SERIES[m], label=m)
            ax.axhline(ref[0], color=INK2, linewidth=1, linestyle="--")
            ax.axhline(ref[1], color="#e34948", linewidth=1, linestyle=":")
            ax.set_xticks(range(len(SCEN))); ax.set_xticklabels(SCEN, fontsize=9)
            style(ax, f"underwriting n_u = {nu} tasks")
        axes[0].set_ylabel(ylab, color=INK2)
        axes[0].set_ylim(0, 1.0)
        axes[-1].legend(frameon=False, fontsize=9, loc="lower right")
        fig.suptitle(f"Phase A: {ylab} by scenario (experience n_e = 200 tasks x 2 simulators; dashed = target,"
                     f" dotted = kill/K level)", fontsize=10, color=INK2, x=0.01, ha="left")
        fig.tight_layout(); fig.savefig(out / fname, dpi=150); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.2), sharey=True)
    for ax, m in zip(axes, SERIES):
        h = g["S0|nu=90|ne=200"][m]["pit_hist"]; tot = sum(h)
        ax.bar([i / 10 + 0.05 for i in range(10)], [x / tot for x in h], width=0.095, color=SERIES[m])
        ax.axhline(0.1, color=INK2, linestyle="--", linewidth=1)
        style(ax, f"{m}: PIT of realised loss (S0, n_u=90)")
    axes[0].set_ylabel("share of forecasts", color=INK2)
    fig.tight_layout(); fig.savefig(out / "pit_S0.png", dpi=150); plt.close(fig)
    print("figures ->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
