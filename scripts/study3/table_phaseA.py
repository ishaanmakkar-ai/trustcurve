"""Tables for Study 3 phase A' (STUDY3.md §A'): predictions P1-P4 and the pre-registered decision rules.

Usage: python scripts/study3/table_phaseA.py results/study3/phaseA/sim_a.json <out.md>
"""

from __future__ import annotations

import json
import sys


def key(c):
    return (c["lam"], c["phi"], c["e"], tuple(c["r"]), c["n_e"])


def main(path, out):
    S = json.load(open(path))
    C = {key(s["cell"]): s for s in S["cells"]}
    L = []
    w = L.append
    R1, R2 = (0.05, 0.4), (0.02, 0.15)
    w("## Detection by source (n_e-independent; shown at n_e = 200, e = 1). Mean share flagged (MC SE ≤ 0.02)\n")
    w("| λ | φ | r | F1 des | F1 non-des | F2p des | F2p non-des | F2s des | F2s non-des | F2p gap | F2s gap | P(H2) F2p | P(H2) F2s | P(H1) F2p | FP F1/F2p/F2s |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for lam in (0.8, 0.5, 0.2):
        for phi in (0.0, 0.05, 0.10):
            for r in (R1, R2):
                s = C[(lam, phi, 1, r, 200)]
                d = lambda f, k: s[f]["det"][k][0]
                w(f"| {lam} | {phi} | {list(r)} | {d('F1','designed'):.2f} | {d('F1','nondesigned'):.2f} | {d('F2p','designed'):.2f} | "
                  f"{d('F2p','nondesigned'):.2f} | {d('F2s','designed'):.2f} | {d('F2s','nondesigned'):.2f} | "
                  f"{s['P']['gap_F2p'][0]:+.2f} | {s['P']['gap_F2s'][0]:+.2f} | {s['P']['H2_F2p'][0]:.2f} | {s['P']['H2_F2s'][0]:.2f} | "
                  f"{s['P']['H1_F2p'][0]:.2f} | {s['F1']['fp'][0]:.2f}/{s['F2p']['fp'][0]:.2f}/{s['F2s']['fp'][0]:.2f} |")
    w("\n## Trap enrichment e = 3 vs e = 1 (λ = 0.5, φ = 0.10, n_e = 200)\n")
    w("| r | e | F2p non-des | F2s non-des | F2p medlog | F2s medlog | F2p bias (flawed) | F2s bias (flawed) | P(H3) F2p | P(H3) F2s |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in (R1, R2):
        for e in (1, 3):
            s = C[(0.5, 0.10, e, r, 200)]
            w(f"| {list(r)} | {e} | {s['F2p']['det']['nondesigned'][0]:.2f} | {s['F2s']['det']['nondesigned'][0]:.2f} | "
              f"{s['F2p']['score']['medlog'][0]:.2f} | {s['F2s']['score']['medlog'][0]:.2f} | {s['F2p']['score']['bias_flawed'][0]:+.2f} | "
              f"{s['F2s']['score']['bias_flawed'][0]:+.2f} | {s['P']['H3_F2p'][0]:.2f} | {s['P']['H3_F2s'][0]:.2f} |")
    w("\n## Pricing by n_e (λ = 0.5, φ = 0.10, e = 1)\n")
    w("| r | n_e | cost $ | Spearman F1/F2p/F2s/F3 | medlog F1/F2p/F2s/F3 | coverage F1/F2p/F2s/F3 | P(H3) F2p/F2s | P(H4) F2p/F2s |")
    w("|---|---|---|---|---|---|---|---|")
    for r in (R1, R2):
        for n in (100, 200, 400):
            s = C[(0.5, 0.10, 1, r, n)]
            g = lambda m: "/".join(f"{s[f]['score'][m][0]:.2f}" for f in ("F1", "F2p", "F2s", "F3"))
            w(f"| {list(r)} | {n} | {s['cost_usd']} | {g('spearman')} | {g('medlog')} | {g('coverage')} | "
              f"{s['P']['H3_F2p'][0]:.2f}/{s['P']['H3_F2s'][0]:.2f} | {s['P']['H4_F2p'][0]:.2f}/{s['P']['H4_F2s'][0]:.2f} |")
    w("\n## Single-target flaws: detection by target type (pooled over λ, φ = 0.10, e = 1, n_e = 200; r = [0.05, 0.4])\n")
    w("| type | F1 | F2p (φ = 0) | F2p (φ = 0.10) | n configs |")
    w("|---|---|---|---|---|")
    types = list(next(iter(C.values()))["F1"]["det_single_target_by_type"])
    for t in types:
        def pooled(f, phi):
            num = den = 0
            for lam in (0.8, 0.5, 0.2):
                m, _, n = C[(lam, phi, 1, R1, 200)][f]["det_single_target_by_type"][t]
                if m is not None:
                    num += m * n; den += n
            return (num / den if den else float("nan")), den
        f1, n = pooled("F1", 0.10); f20, _ = pooled("F2p", 0.0); f21, _ = pooled("F2p", 0.10)
        w(f"| {t} | {f1:.2f} | {f20:.2f} | {f21:.2f} | {n} |")
    w("\n## Maximum P(H3) over all cells, by forecaster variant\n")
    for v in ("F2p", "F2s"):
        best = max(S["cells"], key=lambda s: s["P"][f"H3_{v}"][0])
        w(f"- {v}: {best['P'][f'H3_{v}'][0]:.2f} at {best['cell']}")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
