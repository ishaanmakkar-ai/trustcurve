"""Study 3 C′ scoring (STUDY3.md §C′3, §C′6, S1): RQ1 from the frozen blind detection, RQ2/RQ4 estimates against
realised experience loss, H3/H3b secondary, RQ3 difference-in-differences, RQ5 subset, and the S1 economics.

Everything here reads only frozen forecasts, the frozen detection and experience records; no sealed file.
"""

from __future__ import annotations

import numpy as np
from scipy import stats as sps

from trustcurve.study3.configs import CONFIGS3, H2_SET, H2_SET_STRICT

FLOOR = 0.05
DES = [c for c, v in CONFIGS3.items() if v.source == "designed"]
FLAWED = [c for c, v in CONFIGS3.items() if v.source != "clean"]
NONDES_8 = [c for c, v in CONFIGS3.items() if v.source in ("external", "mechanical")]


def realised(exp_recs: dict) -> dict:
    return {c: float(np.mean([r["loss"] for r in recs])) for c, recs in exp_recs.items() if recs}


def _abslog(f, y):
    return abs(np.log(max(f, FLOOR)) - np.log(max(y, FLOOR)))


def pricing(fc: dict, real: dict, B: int = 2000, seed: int = 0) -> dict:
    cs = sorted(set(fc) & set(real))
    f = np.array([fc[c]["point"] for c in cs]); y = np.array([real[c] for c in cs])
    err = np.array([_abslog(a, b) for a, b in zip(f, y)])
    cov = [fc[c]["lo90"] <= real[c] <= fc[c]["hi90"] for c in cs if "lo90" in fc[c] and fc[c]["lo90"] is not None]
    bias = [np.log(max(fc[c]["point"], FLOOR)) - np.log(max(real[c], FLOOR)) for c in cs if c in FLAWED]
    rng = np.random.default_rng(seed)
    sp_b, ml_b = [], []
    for _ in range(B):
        i = rng.integers(0, len(cs), len(cs))
        if np.ptp(y[i]) > 0 and np.ptp(f[i]) > 0:
            sp_b.append(sps.spearmanr(f[i], y[i]).statistic)
        ml_b.append(np.median(err[i]))
    sp = float(sps.spearmanr(f, y).statistic) if np.ptp(y) > 0 and np.ptp(f) > 0 else 0.0
    return {"n": len(cs), "spearman": sp, "spearman_ci90": [float(np.quantile(sp_b, q)) for q in (0.05, 0.95)] if sp_b else None,
            "medlog": float(np.median(err)), "medlog_ci90": [float(np.quantile(ml_b, q)) for q in (0.05, 0.95)],
            "coverage": float(np.mean(cov)) if cov else None, "median_log_bias_flawed": float(np.median(bias)) if bias else None,
            "per_config_abslog": dict(zip(cs, map(float, err)))}


def h3(fc2, fc1, real) -> dict:
    p2, p1 = pricing(fc2, real, B=200), pricing(fc1, real, B=200)
    e2, e1 = p2["per_config_abslog"], p1["per_config_abslog"]
    cs = sorted(set(e2) & set(e1))
    plus = sum(e2[c] < e1[c] for c in cs); minus = sum(e2[c] > e1[c] for c in cs)
    p = float(sps.binom.sf(plus - 1, plus + minus, 0.5)) if plus + minus else 1.0
    return {"H3": p2["medlog"] <= 0.5 * p1["medlog"] and p2["spearman"] >= p1["spearman"] + 0.3,
            "H3b_sign_p": p, "H3b": p < 0.05, "plus": plus, "minus": minus}


def rq1(det: dict, h2_primary: list = None) -> dict:
    h2_primary = h2_primary or H2_SET
    F2, F13, F11 = det["F2"], det["F1_3"], det["F1_1"]
    share = lambda d, cs: float(np.mean([d[c]["flag_primary"] for c in cs]))
    b = sum(F2[c]["flag_primary"] and not F13[c]["flag_primary"] for c in FLAWED)
    cc = sum(F13[c]["flag_primary"] and not F2[c]["flag_primary"] for c in FLAWED)
    mc = float(sps.binom.sf(b - 1, b + cc, 0.5)) if b + cc else 1.0

    def did(d):
        return share(d, DES) - share(d, h2_primary)
    rng = np.random.default_rng(1)
    boot = []
    for _ in range(2000):
        ds = list(rng.choice(DES, len(DES))); nd = list(rng.choice(h2_primary, len(h2_primary)))
        boot.append((share(F2, ds) - share(F2, nd)) - (share(F13, ds) - share(F13, nd)))
    return {"H1_share": share(F2, DES), "H1": share(F2, DES) >= 0.7,
            "H2_share": share(F2, h2_primary), "H2": share(F2, h2_primary) >= 0.5, "H2_set": h2_primary,
            "H2_strict_share": share(F2, H2_SET_STRICT), "H2_8_share": share(F2, NONDES_8),
            "F1_3_nondes_share": share(F13, h2_primary), "F1_1_nondes_share": share(F11, h2_primary),
            "fp": {c: F2[c]["flag_primary"] for c in ("C1", "C2", "C3")},
            "fp_F1_3": {c: F13[c]["flag_primary"] for c in ("C1", "C2", "C3")},
            "mcnemar_F2_vs_F1_3": {"b": b, "c": cc, "p": mc},
            "did": did(F2) - did(F13), "did_ci90": [float(np.quantile(boot, q)) for q in (0.05, 0.95)],
            "H5_gap_F2": did(F2), "H5": did(F2) <= 0.25,
            "by_source": {s: share(F2, [c for c, v in CONFIGS3.items() if v.source == s])
                          for s in ("designed", "external", "mechanical", "natural")},
            "by_source_F1_3": {s: share(F13, [c for c, v in CONFIGS3.items() if v.source == s])
                               for s in ("designed", "external", "mechanical", "natural")}}


def score_all(frozen: dict, exp_recs: dict, exp_recs_absent: dict | None = None) -> dict:
    fc, det = frozen["forecasts"], frozen["detection"]
    real = realised(exp_recs)
    out = {"realised": real, "rq1": rq1(det), "pricing": {f: pricing(v, real) for f, v in fc.items()},
           "h3": h3(fc["F2"], fc["F1_3"], real), "h3_vs_F1_1": h3(fc["F2"], fc["F1_1"], real)}
    for f in out["pricing"].values():
        f.pop("per_config_abslog", None)
    if exp_recs_absent:
        ra = realised(exp_recs_absent)
        out["rq5"] = {f: {k: v for k, v in pricing(fc[f], ra, B=500).items() if k != "per_config_abslog"}
                      for f in ("F1_3", "F2") if f in fc}
    return out
