"""Phase C figures (committed before any experience outcome). Regenerates from the frozen forecasts + scored results.

Usage: python scripts/study2/fig_phaseC.py <forecasts_frozen.json> <score_c.json> <out_dir>
  forecast_vs_realised.png : per configuration, frozen M2 point forecast (x) with its 90% predictive interval vs the
                             realised pure premium in the experience period (y); identity line; pre-registered 13 vs
                             added configurations; symlog axes ($/conversation; many configurations are at $0).
  by_simulator.png         : realised pure premium per configuration under each simulator (S, L, bridge H).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COL = {"pre13": "#2a78d6", "extended": "#eb6834"}
SIMC = {"S": "#2a78d6", "L": "#eb6834", "H": "#1baf7a"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9); ax.grid(color=GRID, linewidth=0.8); ax.set_axisbelow(True)


def main(fc_path, score_path, out_dir):
    F = json.load(open(fc_path))["configs"]; S = json.load(open(score_path)); out = Path(out_dir)
    R = {**S["extended"]["realised"]}
    fig, ax = plt.subplots(figsize=(8.2, 6.4))
    hi = max([R.get(c, 0) for c in F] + [F[c]["combined"]["pred_hi90"] for c in F] + [1.0]) * 1.3
    ax.plot([0, hi], [0, hi], color=INK2, linewidth=1, linestyle="--", label="forecast = realised")
    for g in ("pre13", "extended"):
        cs = [c for c in F if F[c].get("group") == g and c in R]
        if not cs:
            continue
        x = [F[c]["combined"]["point"] for c in cs]; y = [R[c] for c in cs]
        lo = [F[c]["combined"]["point"] - F[c]["combined"]["pred_lo90"] for c in cs]
        up = [F[c]["combined"]["pred_hi90"] - F[c]["combined"]["point"] for c in cs]
        ax.errorbar(x, y, xerr=[lo, up], fmt="o", ms=7, color=COL[g], ecolor=COL[g], elinewidth=1.2, alpha=0.9,
                    capsize=0, label={"pre13": "pre-registered 13 (K2 set)", "extended": "added after screening"}[g])
    ranked = sorted(F, key=lambda c: -(R.get(c, 0) + F[c]["combined"]["point"]))
    for c in ranked[:8]:
        if c in R:
            ax.annotate(c, (F[c]["combined"]["point"], R[c]), textcoords="offset points", xytext=(6, 4), fontsize=8, color=INK)
    ax.set_xscale("symlog", linthresh=1.0); ax.set_yscale("symlog", linthresh=1.0)
    ax.set_xlim(-0.2, hi); ax.set_ylim(-0.2, hi)
    ax.set_xlabel("frozen forecast: pure premium, $ per conversation (90% predictive interval)", color=INK2)
    ax.set_ylabel("realised in the experience period, $ per conversation", color=INK2)
    k2 = S["primary"]["k2"]; ke = S["extended"]["k2"]
    style(ax, f"Forecast vs realised commission loss (K2 set: Spearman {k2['spearman']:.2f}, coverage "
              f"{k2['coverage']:.2f}; all: Spearman {ke['spearman']:.2f})" if k2["spearman"] == k2["spearman"] else
              "Forecast vs realised commission loss (K2 set: Spearman undetermined)")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout(); fig.savefig(out / "forecast_vs_realised.png", dpi=160); plt.close(fig)
    sims = S.get("rq5_by_simulator", {})
    cs = sorted(F, key=lambda c: -R.get(c, 0))
    fig, ax = plt.subplots(figsize=(10, 4.2)); w = 0.27
    for i, s in enumerate(("S", "L", "H")):
        if s not in sims:
            continue
        ys = [sims[s]["realised"].get(c, float("nan")) for c in cs]
        ax.bar([j + (i - 1) * w for j in range(len(cs))], ys, width=w - 0.03, color=SIMC[s],
               label={"S": "Sonnet 5.5 customer", "L": "gpt-6-luna customer", "H": "Haiku customer (bridge, 60 tasks)"}[s])
    ax.set_xticks(range(len(cs))); ax.set_xticklabels(cs, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("realised $ per conversation", color=INK2)
    style(ax, "Realised commission loss by customer simulator"); ax.legend(frameon=False, fontsize=9)
    fig.tight_layout(); fig.savefig(out / "by_simulator.png", dpi=160); plt.close(fig)
    print("figures ->", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
