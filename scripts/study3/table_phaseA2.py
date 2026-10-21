"""Tables and decision-rule evaluation for Study 3 phase A' loop 2 (STUDY3.md §"A' loop 2").

Usage: python scripts/study3/table_phaseA2.py results/study3/phaseA/sim_a2.json <out.md> <decisions.json>
"""

from __future__ import annotations

import json
import sys

R1, R2 = (0.05, 0.4), (0.02, 0.15)


def key(c):
    return (c["lam"], c["phi"], c["e"], tuple(c["r"]), c["n_e"], c["S"], c["R"])


def main(path, out, dec_out):
    S = json.load(open(path))
    C = {key(s["cell"]): s for s in S["cells"]}
    m = lambda s, v, k: s[v][k][0]
    L = []; w = L.append
    w("## Detection and its discrimination (n_e = 200, e = 1)\n")
    w("| λ | φ | r | S | R | F1 non-des | F2p des | F2p non-des | P(H2) F1 | P(H2) F2p | H2 discrim. F2p | McNemar power F2p | cost $ |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for lam in (0.5, 0.2):
        for phi in (0.0, 0.10):
            for r in (R1, R2):
                for Rr in (1, 3):
                    s = C[(lam, phi, 1, r, 200, "A", Rr)]
                    w(f"| {lam} | {phi} | {list(r)} | A | {Rr} | {s['F1']['det_nondes'][0]:.2f} | {m(s,'F2p','det_des'):.2f} | "
                      f"{m(s,'F2p','det_nondes'):.2f} | {s['F1']['H2'][0]:.2f} | {m(s,'F2p','H2'):.2f} | {s['F2p']['H2_discrimination']:+.2f} | "
                      f"{m(s,'F2p','mcnemar'):.2f} | {s['cost_usd']} |")
    w("\n## Single-target detection by type (λ = 0.5, n_e = 200, e = 1, S_A)\n")
    w("| r | R | φ | cabin F1/F2p | bags F1/F2p | book F1/F2p | certificate F1/F2p | statement F1/F2p |")
    w("|---|---|---|---|---|---|---|---|")
    for r in (R1, R2):
        for Rr in (1, 3):
            for phi in (0.0, 0.10):
                s = C[(0.5, phi, 1, r, 200, "A", Rr)]
                bt = s["by_type"]
                w(f"| {list(r)} | {Rr} | {phi} | " + " | ".join(f"{bt['F1'][t][0]:.2f}/{bt['F2p'][t][0]:.2f}"
                                                              for t in ("cabin", "bags", "book", "certificate", "statement")) + " |")
    w("\n## Pricing: F2 vs F1 (λ = 0.5, φ = 0.10, e = 1)\n")
    w("| S | R | r | n_e | blind share | medlog F1/F2p/F2s | Spearman F1/F2p/F2s | P(F2p medlog < F1) | pricing sign power F2p/F2s | P(ΔSpearman ≥ 0.1) F2p | P(H3) F2p | cost $ |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for Sv in ("A", "B"):
        for Rr in (1, 3):
            for r in (R1, R2):
                for n in (100, 200, 400):
                    s = C[(0.5, 0.10, 1, r, n, Sv, Rr)]
                    w(f"| {Sv} | {Rr} | {list(r)} | {n} | {s['blind_share'][0]:.2f} | {s['F1']['medlog'][0]:.2f}/{m(s,'F2p','medlog'):.2f}/{m(s,'F2s','medlog'):.2f} | "
                      f"{s['F1']['spearman'][0]:.2f}/{m(s,'F2p','spearman'):.2f}/{m(s,'F2s','spearman'):.2f} | {m(s,'F2p','f2_better_medlog'):.2f} | "
                      f"{m(s,'F2p','pricing_sign'):.2f}/{m(s,'F2s','pricing_sign'):.2f} | {m(s,'F2p','sp_plus01'):.2f} | {m(s,'F2p','H3'):.2f} | {s['cost_usd']} |")
    w("\n## Trap enrichment (λ = 0.5, φ = 0.10, n_e = 200, S_A)\n")
    w("| r | R | e | F2p non-des | F2s non-des | F2p medlog | F2s medlog | F2p bias | F2s bias |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in (R1, R2):
        for Rr in (1, 3):
            for e in (1, 3):
                s = C[(0.5, 0.10, e, r, 200, "A", Rr)]
                w(f"| {list(r)} | {Rr} | {e} | {m(s,'F2p','det_nondes'):.2f} | {m(s,'F2s','det_nondes'):.2f} | {m(s,'F2p','medlog'):.2f} | "
                  f"{m(s,'F2s','medlog'):.2f} | {m(s,'F2p','bias_flawed'):+.2f} | {m(s,'F2s','bias_flawed'):+.2f} |")
    shares = [s["blind_share"][0] for s in S["cells"]]
    n_hi = sum(s["share_ge_05"] * s["reps"] for s in S["cells"])
    w(f"\n## Blind-spot loss share\n\nAcross all 192 cells the mean share of true flaw loss on types F1 barely exercises is "
      f"{min(shares):.2f}–{max(shares):.2f}; replications with share ≥ 0.5: {int(n_hi)} of {192 * S['meta']['reps']}.")
    hs = [s for s in S["cells"] if s["cell"]["S"] == "B" and s["F2p"]["given_share_ge_05"]["H3"][2] >= 20]
    if hs:
        w("\nS_B cells with ≥ 20 such replications, P(H3 | share ≥ 0.5) F2p: " +
          ", ".join(f"{s['F2p']['given_share_ge_05']['H3'][0]:.2f} (n {s['F2p']['given_share_ge_05']['H3'][2]})" for s in hs[:12]))

    # pre-registered decision rules
    dec = {}
    d1, d2 = C[(0.5, 0.10, 1, R1, 200, "A", 1)]["F2p"]["H2_discrimination"], C[(0.5, 0.10, 1, R2, 200, "A", 1)]["F2p"]["H2_discrimination"]
    r_star = R1 if d1 >= d2 else R2
    dec["flaw_rate_range"] = {"choice": list(r_star), "H2_discrimination": {str(list(R1)): d1, str(list(R2)): d2}}
    mc1, mc3 = (C[(0.5, 0.10, 1, r_star, 200, "A", Rr)]["F2p"]["mcnemar"][0] for Rr in (1, 3))
    R_star = 3 if mc3 - mc1 >= 0.15 else 1
    dec["R"] = {"choice": R_star, "mcnemar_power": {"R1": mc1, "R3": mc3}}
    s3 = C[(0.5, 0.10, 3, r_star, 200, "A", R_star)]
    dml, ddet = s3["F2p"]["medlog"][0] - s3["F2s"]["medlog"][0], s3["F2p"]["det_nondes"][0] - s3["F2s"]["det_nondes"][0]
    dec["split"] = {"adopt": bool(dml >= 0.1 and ddet <= 0.1), "medlog_gain": round(dml, 3), "detection_loss": round(ddet, 3)}
    phi_star = None
    for phi in (0.0, 0.10):
        bt = C[(0.5, phi, 1, r_star, 200, "A", R_star)]["by_type"]["F2p"]
        if all(bt[t][0] >= 0.3 for t in ("cabin", "bags", "book")):
            phi_star = phi; break
    dec["phi"] = {"choice": phi_star, "per_type_at_0.10": {t: C[(0.5, 0.10, 1, r_star, 200, "A", R_star)]["by_type"]["F2p"][t][0]
                                                         for t in ("cabin", "bags", "book")}}
    ps = {n: C[(0.5, 0.10, 1, r_star, n, "A", R_star)]["F2p"]["pricing_sign"][0] for n in (100, 200, 400)}
    dec["n_e"] = {"choice": next(n for n in (100, 200, 400) if ps[400] - ps[n] <= 0.1), "pricing_sign_power": ps}
    h3b = [s["F2p"]["given_share_ge_05"]["H3"] for s in S["cells"] if s["cell"]["S"] == "B" and s["F2p"]["given_share_ge_05"]["H3"][2] >= 20]
    dec["H3b_trigger"] = {"fires": (not h3b) or all(x[0] < 0.2 for x in h3b), "n_cells_evaluable": len(h3b),
                          "note": "no S_B cell had >= 20 replications with share >= 0.5" if not h3b else ""}
    lam5 = [s for s in S["cells"] if s["cell"]["lam"] == 0.5]
    dec["K1prime"] = {"fires": all(s["F2p"]["H2_discrimination"] < 0.3 and s["F2p"]["pricing_sign"][0] < 0.5 for s in lam5),
                      "max_H2_discrimination": max(s["F2p"]["H2_discrimination"] for s in lam5),
                      "max_pricing_sign_power": max(s["F2p"]["pricing_sign"][0] for s in lam5)}
    w("\n## Pre-registered decision rules (loop 2)\n\n```json\n" + json.dumps(dec, indent=1) + "\n```")
    open(out, "w").write("\n".join(L) + "\n"); json.dump(dec, open(dec_out, "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main(*sys.argv[1:4])
