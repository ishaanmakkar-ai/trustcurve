"""Phase C figures v2 (POST-HOC, after review 8 #10; the frozen v1 figures are kept unchanged).

Usage: python scripts/study2/fig_phaseC_v2.py <out_dir>
  forecast_vs_realised_v2.png : two panels, pre-registered 13 (K2 set) and the 11 added configurations; every point
                                labelled; within-group Spearman and coverage in the titles; symlog axes.
  by_simulator_same_tasks.png : realised $/conversation on the SAME 60 bridge tasks under the Haiku, Sonnet and luna
                                customers, for the 20 bridge configurations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
COL = {"pre13": "#2a78d6", "extended": "#eb6834"}
SIMC = {"H": "#1baf7a", "S": "#2a78d6", "L": "#eb6834"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=10.5, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8.5); ax.grid(color=GRID, linewidth=0.8); ax.set_axisbelow(True)


def main(out_dir):
    out = Path(out_dir)
    F = json.load(open(ROOT / "results/study2/forecasts_frozen.json"))["configs"]
    S = json.load(open(ROOT / "results/study2/phaseC/score_c.json"))
    P = json.load(open(ROOT / "results/study2/phaseC/posthoc_review8.json"))
    R = S["extended"]["realised"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8), sharey=True)
    hi = max([R[c] for c in R] + [F[c]["combined"]["pred_hi90"] for c in F]) * 1.4
    for ax, g, key in ((axes[0], "pre13", "pre13"), (axes[1], "extended", "ext11")):
        cs = sorted([c for c in F if F[c]["group"] == g], key=lambda c: F[c]["combined"]["point"])
        ax.plot([0, hi], [0, hi], color=INK2, linewidth=1, linestyle="--")
        for i, c in enumerate(cs):
            f = F[c]["combined"]; x, y = f["point"], R[c]
            ax.plot([f["pred_lo90"], f["pred_hi90"]], [y, y], color=COL[g], linewidth=1.3, alpha=0.55)
            ax.plot([x], [y], "o", ms=7, color=COL[g], mec="white", mew=1.5)
            ax.annotate(c, (x, y), textcoords="offset points", xytext=(6, 5 + (i % 3) * 6), fontsize=7.5, color=INK)
        st = P[key]
        style(ax, f"{'Pre-registered 13 (K2 set)' if g == 'pre13' else '11 configurations added after screening'}: "
                  f"Spearman {st['spearman']:.2f}, 90% coverage {st['coverage']:.2f}")
        ax.set_xscale("symlog", linthresh=1.0); ax.set_yscale("symlog", linthresh=1.0)
        ax.set_xlim(-0.2, hi); ax.set_ylim(-0.2, hi)
        ax.set_xlabel("frozen forecast, $ per conversation (bar: 90% predictive interval)", color=INK2)
    axes[0].set_ylabel("realised in the experience period, $ per conversation", color=INK2)
    fig.suptitle("Forecast vs realised commission loss. Dashed: forecast = realised. Post-hoc layout (review 8); "
                 "values from the frozen forecasts and frozen scorer.", fontsize=9, color=INK2, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(out / "forecast_vs_realised_v2.png", dpi=160); plt.close(fig)
    B = S["bridge_same_tasks"]; cs = sorted(B, key=lambda c: -(B[c]["S"] + B[c]["L"]))
    fig, ax = plt.subplots(figsize=(11, 4.2)); w = 0.27
    for i, s in enumerate(("H", "S", "L")):
        ax.bar([j + (i - 1) * w for j in range(len(cs))], [B[c][s] for c in cs], width=w - 0.03, color=SIMC[s],
               label={"H": "Haiku customer (underwriting simulator)", "S": "Sonnet 5.5 customer", "L": "gpt-6-luna customer"}[s])
    ax.set_xticks(range(len(cs))); ax.set_xticklabels(cs, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("realised $ per conversation (same 60 tasks)", color=INK2)
    bt = P["bridge_paired_events"]
    style(ax, f"Same 60 tasks, three customer simulators: events H {bt['events']['H']}, S {bt['events']['S']}, "
              f"L {bt['events']['L']} (paired H vs S p = {bt['H_vs_S_p_mcnemar_exact']:.2f}). One capped event = $33")
    ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout(); fig.savefig(out / "by_simulator_same_tasks.png", dpi=160); plt.close(fig)
    print("figures ->", out)


if __name__ == "__main__":
    main(sys.argv[1])
