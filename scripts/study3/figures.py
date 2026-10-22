"""Study 3 E′ figures: forecast vs realised loss per forecaster (small multiples), from committed files only.

Colours: the dataviz reference categorical palette, slots 1-5 in fixed order (pre-validated in the skill's palette.md;
the validator script needs Node, which is not installed here). Identity is never colour-alone: each flaw source also
has its own marker shape, and the legend names them.

Usage: python scripts/study3/figures.py [forecasts_frozen.json score_c.json out_dir]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from trustcurve.study3.configs import CONFIGS3  # noqa: E402

SRC = {"clean": ("#2a78d6", "o"), "designed": ("#eb6834", "s"), "external": ("#1baf7a", "^"),
       "mechanical": ("#eda100", "D"), "natural": ("#e87ba4", "v")}
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
ORDER = [("F0", "F0 outside-in (flat)"), ("F0q", "F0q questionnaire"), ("F1_1", "F1 generic, 1 run"),
         ("F1_3", "F1 generic, 3 runs"), ("F2", "F2 designed"), ("F3", "F3 underwriters")]
FLOOR = 0.05


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8); ax.grid(color=GRID, linewidth=0.7); ax.set_axisbelow(True)


def forecast_vs_realised(frozen, score, out_png):
    fc, real, pr = frozen["forecasts"], score["realised"], score["pricing"]
    panels = [(k, t) for k, t in ORDER if k in fc]
    vals = [max(v, FLOOR) for v in real.values()] + [max(fc[k][c]["point"], FLOOR) for k, _ in panels for c in fc[k]]
    lo, hi = min(vals) / 1.6, max(vals) * 1.6
    ncol = 3; nrow = (len(panels) + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(12.5, 4.1 * nrow), sharex=True, sharey=True, facecolor=SURF)
    axes = axes.ravel()
    for ax, (k, title) in zip(axes, panels):
        ax.plot([lo, hi], [lo, hi], color=INK2, linewidth=1, linestyle="--", zorder=1)
        for c, f in fc[k].items():
            if c not in real:
                continue
            col, mk = SRC[CONFIGS3[c].source]
            x, y = max(f["point"], FLOOR), max(real[c], FLOOR)
            if f.get("lo90") is not None and f.get("hi90") is not None:
                ax.plot([max(f["lo90"], FLOOR), max(f["hi90"], FLOOR)], [y, y], color=col, linewidth=2, alpha=0.45,
                        solid_capstyle="round", zorder=2)
            ax.plot([x], [y], marker=mk, markersize=8, color=col, markeredgecolor=SURF, markeredgewidth=2, linestyle="none", zorder=3)
        p = pr.get(k, {})
        sub = (f"Spearman {p.get('spearman', float('nan')):.2f} · median |log err| {p.get('medlog', float('nan')):.2f}"
               + (f" · 90% cov {p['coverage']:.2f}" if p.get("coverage") is not None else ""))
        style(ax, f"{title}\n{sub}")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    for ax in axes[len(panels):]:
        ax.axis("off")
    for ax in axes[(nrow - 1) * ncol:]:
        ax.set_xlabel("frozen forecast, $ per conversation (bar: 90% interval)", color=INK2, fontsize=9)
    for ax in axes[::ncol]:
        ax.set_ylabel("realised, $ per conversation", color=INK2, fontsize=9)
    handles = [plt.Line2D([], [], marker=m, color=c, markeredgecolor=SURF, markeredgewidth=1.5, markersize=8, linestyle="none",
                          label=s) for s, (c, m) in SRC.items()]
    fig.legend(handles=handles, loc="upper right", ncol=5, frameon=False, fontsize=9, labelcolor=INK2)
    fig.suptitle("Study 3: frozen forecasts vs realised loss, 20 agents. Dashed: forecast = realised.",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(out_png, dpi=160, facecolor=SURF); plt.close(fig)


def detection_by_source(score, out_png):
    r = score["rq1"]; srcs = ["designed", "external", "mechanical", "natural"]
    fig, ax = plt.subplots(figsize=(7.5, 3.6), facecolor=SURF)
    w = 0.36
    for i, (key, lab, col) in enumerate((("by_source_F1_3", "F1 generic (3 runs)", "#2a78d6"), ("by_source", "F2 designed", "#eb6834"))):
        xs = [j + (i - 0.5) * w for j in range(len(srcs))]
        ax.bar(xs, [r[key][s] for s in srcs], width=w - 0.04, color=col, label=lab)
    ax.set_xticks(range(len(srcs))); ax.set_xticklabels(srcs); ax.set_ylim(0, 1)
    ax.set_ylabel("share of configurations flagged", color=INK2, fontsize=9)
    style(ax, "Detection by flaw source (frozen, blind sign test vs C0)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2)
    fig.tight_layout(); fig.savefig(out_png, dpi=160, facecolor=SURF); plt.close(fig)


def main(fz=None, sc=None, out=None):
    fz = Path(fz or ROOT / "results/study3/forecasts_frozen.json"); sc = Path(sc or ROOT / "results/study3/phaseC/score_c.json")
    out = Path(out or ROOT / "results/study3/figures"); out.mkdir(parents=True, exist_ok=True)
    frozen, score = json.loads(fz.read_text()), json.loads(sc.read_text())
    forecast_vs_realised(frozen, score, out / "forecast_vs_realised.png")
    detection_by_source(score, out / "detection_by_source.png")
    print("figures ->", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
