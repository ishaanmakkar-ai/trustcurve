"""Tables and decision rules for Study 3 phase A' loop 3 (STUDY3.md §"A' loop 3").

Usage: python scripts/study3/table_phaseA3.py results/study3/phaseA/sim_a3.json <out.md> <decisions.json>
"""

from __future__ import annotations

import json
import sys


def main(path, out, dec_out):
    S = json.load(open(path))
    C = {(s["cell"]["lam"], s["cell"]["phi"], s["cell"]["R"], s["cell"]["size"]): s for s in S["cells"]}
    L = []; w = L.append
    g = lambda s, v, k: s[v][k][0]
    w("## Loop 3: detection, shared-assumption gap and pricing (F2 = adopted split; F2p in brackets)\n")
    w("| λ | φ | R | configs | F1 non-des | F2 des | F2 non-des | non-des anticipated / unanticipated | gap [F2p] | P(H1) | P(H2) | H2 discrim. | P(H5) | McNemar | medlog F1/F2 [F2p] | Spearman F1/F2 | H3b power [F2p] | P(H3) | cost $ |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for lam in (0.8, 0.5, 0.2):
        for phi in (0.0, 0.10):
            for R in (1, 3):
                for n in (18, 30):
                    s = C[(lam, phi, R, n)]
                    w(f"| {lam} | {phi} | {R} | {n} | {s['F1']['det_nondes'][0]:.2f} | {g(s,'F2s','det_des'):.2f} | {g(s,'F2s','det_nondes'):.2f} | "
                      f"{g(s,'F2s','det_nondes_anticipated'):.2f} / {g(s,'F2s','det_nondes_unanticipated'):.2f} | {g(s,'F2s','gap'):+.2f} [{g(s,'F2p','gap'):+.2f}] | "
                      f"{g(s,'F2s','H1'):.2f} | {g(s,'F2s','H2'):.2f} | {s['F2s']['H2_discrimination']:+.2f} | {g(s,'F2s','H5'):.2f} | {g(s,'F2s','mcnemar'):.2f} | "
                      f"{s['F1']['medlog'][0]:.2f}/{g(s,'F2s','medlog'):.2f} [{g(s,'F2p','medlog'):.2f}] | {s['F1']['spearman'][0]:.2f}/{g(s,'F2s','spearman'):.2f} | "
                      f"{g(s,'F2s','H3b_sign'):.2f} [{g(s,'F2p','H3b_sign'):.2f}] | {g(s,'F2s','H3'):.2f} | {s['cost_usd']} |")
    dec = {}
    ref = lambda n: C[(0.5, 0.10, 3, n)]["F2s"]
    p7 = (ref(30)["H3b_sign"][0] - ref(18)["H3b_sign"][0] >= 0.1 and
          abs(ref(30)["H2_discrimination"] - ref(18)["H2_discrimination"]) <= 0.05)
    dec["A'-P7 / size"] = {"P7_holds": p7, "choice": 30 if p7 else 18,
                           "H3b_power": {"18": ref(18)["H3b_sign"][0], "30": ref(30)["H3b_sign"][0]},
                           "H2_discrimination": {"18": ref(18)["H2_discrimination"], "30": ref(30)["H2_discrimination"]}}
    n = dec["A'-P7 / size"]["choice"]
    gaps = {lam: C[(lam, 0.10, 3, n)]["F2s"]["gap"][0] for lam in (0.8, 0.5, 0.2)}
    h5 = {lam: C[(lam, 0.10, 3, n)]["F2s"]["H5"][0] for lam in (0.8, 0.5, 0.2)}
    dec["A'-P5"] = {"holds": gaps[0.2] - gaps[0.8] >= 0.15, "gap_by_lambda": gaps}
    dec["A'-P6"] = {"holds": h5[0.2] < 0.5, "P_H5_by_lambda": h5}
    dec["H5_informative"] = abs(h5[0.8] - h5[0.2]) >= 0.3
    dec["H3b"] = {"power_at_lambda_0.5": ref(n)["H3b_sign"][0], "recommend_as_test": ref(n)["H3b_sign"][0] >= 0.5}
    w("\n## Pre-registered decision rules (loop 3)\n\n```json\n" + json.dumps(dec, indent=1) + "\n```")
    open(out, "w").write("\n".join(L) + "\n"); json.dump(dec, open(dec_out, "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main(*sys.argv[1:4])
