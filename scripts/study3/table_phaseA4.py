"""Tables and pre-registered decision rules for Study 3 phase A' loop 4 (STUDY3.md §"A' loop 4", commit 9bbf26c).

Usage: python scripts/study3/table_phaseA4.py results/study3/phaseA/sim_a4.json <out.md> <decisions.json>
"""

from __future__ import annotations

import json
import sys

R1, R2 = (0.05, 0.4), (0.02, 0.15)


def main(path, out, dec_out):
    S = json.load(open(path))
    C = {(s["cell"]["rho1"], s["cell"]["rho2"], tuple(s["cell"]["r"]), s["cell"]["n_e"]): s for s in S["cells"]}
    L = []; w = L.append
    pm = lambda s, f, m: s["pricing"][f][m][0]
    w("## Pricing vs representativeness (n_e = 200)\n")
    w("| r | ρ1 (F1) | ρ2 (F2 rep) | medlog O/F1₁/F1₃/F2 | bias flawed F1₁/F2 | Spearman O/F1₃/F2 | coverage F1₃/F2 | H3b power F2 vs F1₃ | ceiling O vs F1₃ | P(H3) F2 / O |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in (R1, R2):
        for rho1 in (1.0, 0.6, 0.3, 0.0):
            for rho2 in (1.5, 1.0, 0.6, 0.3):
                s = C[(rho1, rho2, r, 200)]; t = s["tests"]
                w(f"| {list(r)} | {rho1} | {rho2} | {pm(s,'O','medlog'):.2f}/{pm(s,'F1_1','medlog'):.2f}/{pm(s,'F1_3','medlog'):.2f}/{pm(s,'F2','medlog'):.2f} | "
                  f"{pm(s,'F1_1','bias_flawed'):+.2f}/{pm(s,'F2','bias_flawed'):+.2f} | {pm(s,'O','spearman'):.2f}/{pm(s,'F1_3','spearman'):.2f}/{pm(s,'F2','spearman'):.2f} | "
                  f"{pm(s,'F1_3','cov'):.2f}/{pm(s,'F2','cov'):.2f} | {t['H3b'][0]:.2f} | {t['H3b_ceiling'][0]:.2f} | {t['H3_F2'][0]:.2f} / {t['H3_O'][0]:.2f} |")
    w("\n## Detection, exposure-matched, S0 per-task unit (ρ2 = 1, n_e = 200; detection does not depend on n_e)\n")
    w("| r | ρ1 | F1₁ non-des | F1₃ des / non-des | F2 des / non-des | McNemar matched (run-level) | McNemar unmatched | P(H2) F2 / F1₃ | DiD mean (run-level) | DiD SD | DiD 90% width | FP F1₃/F2 |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in (R1, R2):
        for rho1 in (1.0, 0.6, 0.3, 0.0):
            s = C[(rho1, 1.0, r, 200)]; d = s["detection"]; t = s["tests"]
            w(f"| {list(r)} | {rho1} | {d['F1_1']['nondes'][0]:.2f} | {d['F1_3']['des'][0]:.2f} / {d['F1_3']['nondes'][0]:.2f} | {d['F2']['des'][0]:.2f} / {d['F2']['nondes'][0]:.2f} | "
              f"{t['mcnemar_matched'][0]:.2f} ({t['mcnemar_matched_run'][0]:.2f}) | {t['mcnemar_unmatched'][0]:.2f} | {t['H2_F2'][0]:.2f} / {t['H2_F1_3'][0]:.2f} | "
              f"{t['did'][0]:+.2f} ({t['did_run'][0]:+.2f}) | {s['did_sd']:.2f} | {s['did_w90']:.2f} | {d['F1_3']['fp'][0]:.3f}/{d['F2']['fp'][0]:.3f} |")
    w("\n## Detection vs realised firing rate (pooled over ρ1 = 1 cells, both r ranges, all ρ2 and n_e)\n")
    w("| r bin | F1₃ flagged | F2 flagged | n |")
    w("|---|---|---|---|")
    agg = {}
    for s in S["cells"]:
        if s["cell"]["rho1"] != 1.0:
            continue
        for f in ("F1_3", "F2"):
            for i, b in enumerate(s["curve"][f]):
                a = agg.setdefault((f, i), [0, 0, b["bin"]]); a[0] += b["flagged"]; a[1] += b["n"]
    for i in range(4):
        a1, a2 = agg[("F1_3", i)], agg[("F2", i)]
        w(f"| {a1[2]} | {a1[0] / max(a1[1], 1):.2f} | {a2[0] / max(a2[1], 1):.2f} | {a1[1]} |")
    w("\n## Cost by n_e (full line, estimate; prices to be rechecked)\n")
    for n in (100, 200, 400):
        w(f"- n_e = {n}: {C[(1.0, 1.0, R1, n)]['cost']}")

    dec = {"C2": {}, "n_e_rule": {}}
    for r in (R1, R2):
        for n in (100, 200, 400):
            rho = min((1.0, 0.6, 0.3, 0.0), key=lambda x: abs(C[(x, 1.0, r, n)]["pricing"]["F1_1"]["bias_flawed"][0] + 0.7))
            s = C[(rho, 1.0, r, n)]
            dec["C2"][f"{list(r)} n_e={n}"] = {"rho1": rho, "F1_1_bias": s["pricing"]["F1_1"]["bias_flawed"][0],
                                               "H3b": s["tests"]["H3b"][0], "ceiling": s["tests"]["H3b_ceiling"][0]}
    for r in (R1, R2):
        choice = None
        for n in (100, 200, 400):
            c = dec["C2"][f"{list(r)} n_e={n}"]
            if c["H3b"] >= 0.5 and c["H3b"] >= 0.7 * c["ceiling"]:
                choice = n; break
        dec["n_e_rule"][str(list(r))] = {"qualifying_n_e": choice, "n_e": choice or 200,
                                         "RQ2_form": "H3b comparative test" if choice else "estimation with intervals"}
    dec["H3_unreachable"] = {str(list(r)): max(C[(rho, 1.0, r, 200)]["tests"]["H3_O"][0] for rho in (1.0, 0.6, 0.3, 0.0)) < 0.2 for r in (R1, R2)}
    mm = C[(1.0, 1.0, R1, 200)]["tests"]["mcnemar_matched"][0]
    dec["RQ1_form"] = {"matched_mcnemar_power_r1_rho1_1": mm,
                       "primary": "matched McNemar (H2 alongside)" if mm >= 0.6 else "detection-vs-rate curves; H2 stays primary"}
    dec["RQ3"] = {str(list(r)): {"did_w90": C[(1.0, 1.0, r, 200)]["did_w90"],
                                 "label_uninformative": C[(1.0, 1.0, r, 200)]["did_w90"] > 0.4} for r in (R1, R2)}
    dec["P8"] = {"C2_H3b_r1_200": dec["C2"][f"{list(R1)} n_e=200"]["H3b"], "rho1_1_H3b_r1_200": C[(1.0, 1.0, R1, 200)]["tests"]["H3b"][0]}
    dec["P8"]["holds"] = dec["P8"]["C2_H3b_r1_200"] >= 0.5 and dec["P8"]["rho1_1_H3b_r1_200"] <= 0.15
    dec["P9"] = {"matched": mm, "unmatched": C[(1.0, 1.0, R1, 200)]["tests"]["mcnemar_unmatched"][0], "holds": mm <= 0.6}
    dec["P10"] = {"did_w90": C[(1.0, 1.0, R1, 200)]["did_w90"], "holds": C[(1.0, 1.0, R1, 200)]["did_w90"] > 0.4}
    anyok = any(s["tests"]["mcnemar_matched"][0] >= 0.5 for s in S["cells"]) or any(
        v["H3b"] >= 0.5 for v in dec["C2"].values())
    dec["K1prime_fires"] = not anyok
    w("\n## Pre-registered decision rules (loop 4)\n\n```json\n" + json.dumps(dec, indent=1) + "\n```")
    open(out, "w").write("\n".join(L) + "\n"); json.dump(dec, open(dec_out, "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main(*sys.argv[1:4])
