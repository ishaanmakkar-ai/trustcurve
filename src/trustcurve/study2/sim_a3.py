"""Study 2 phase A loop 3 (STUDY2.md §A3): the real underwriting pool's strata, template clusters, configuration x
stratum severity heterogeneity, a directional author shift. Loops 1-2 (sim_a.py) are left untouched.

Usage: python -m trustcurve.study2.sim_a3 <out.json> [reps] [procs]
"""

from __future__ import annotations

import json
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np

from trustcurve.study2.forecast import (BASIC_LIMIT, STRATA, W_DEPLOY, allocation, concordance, crps_samples,
                                        forecast, interval_score, predictive_covered, randomized_pit, spearman)
from trustcurve.study2.sim_a import GH_W, GH_X, REL, SEV_MED, SEV_SIG, capped_lognormal_mean, logit, sig

H = len(STRATA)
BASE_RATE3 = np.array([0.02, 0.01, 0.02, 0.04, 0.02])
U_COUNTS = {90: [45, 23, 3, 18, 1], 45: [23, 11, 2, 9, 0]}            # real pool / screening half
TEMPLATES = {90: [("cancel", 16), ("cancel", 12), ("compensation", 12)], 45: [("cancel", 8), ("cancel", 6), ("compensation", 6)]}
SIGMA_U, SIGMA_G, SIGMA_B, SIGMA_SEV_CH = 1.0, 0.3, 0.2, 0.2
TEMPLATE_MU, TEMPLATE_SD = -0.5, 1.0
SCEN = ("R0", "R2", "R6", "R5")
METHODS = ("M1", "M1c", "M2")


def draw_world(scen, rng):
    C = len(REL)
    alpha = logit(BASE_RATE3 * (0.25 if scen == "R5" else 1.0))
    beta = np.log(REL) + rng.normal(0, SIGMA_B, C)
    gamma = rng.normal(0, SIGMA_G, (C, H))
    sev_ch = np.exp(rng.normal(0, SIGMA_SEV_CH, (C, H)))
    delta = rng.normal(0, 0.5, H) if scen == "R2" else (np.full(H, 0.5) if scen == "R6" else np.zeros(H))
    return dict(alpha=alpha, beta=beta, gamma=gamma, sev_ch=sev_ch, delta=delta)


def true_theta(w):
    C = len(REL); th = np.zeros(C)
    for c in range(C):
        for h in range(H):
            p = np.sum(GH_W * sig(w["alpha"][h] + w["beta"][c] + w["gamma"][c, h] + w["delta"][h] + SIGMA_U * GH_X))
            th[c] += W_DEPLOY[STRATA[h]] * p * capped_lognormal_mean(SEV_MED[h] * w["sev_ch"][c, h], SEV_SIG)
    return th


def underwriting_pool(n_u, rng):
    """Strata at the real counts; template membership and per-task latent (task effect + template effect)."""
    strata = np.concatenate([np.full(k, i) for i, k in enumerate(U_COUNTS[n_u])]).astype(int)
    lat = rng.normal(0, SIGMA_U, len(strata)); cluster = np.array([f"t{i}" for i in range(len(strata))], object)
    used = {h: 0 for h in range(H)}
    for j, (hname, k) in enumerate(TEMPLATES[n_u]):
        h = STRATA.index(hname)
        idx = np.where(strata == h)[0][used[h]: used[h] + k]; used[h] += k
        lat[idx] += rng.normal(TEMPLATE_MU, TEMPLATE_SD)
        cluster[idx] = f"T{j}"
    return strata, lat, cluster


def runs(w, c, strata, lat, rng, delta=False):
    lg = w["alpha"][strata] + w["beta"][c] + w["gamma"][c, strata] + lat + (w["delta"][strata] if delta else 0.0)
    ev = rng.random(len(lg)) < sig(lg)
    sev = np.minimum(np.exp(rng.normal(np.log(SEV_MED[strata] * w["sev_ch"][c, strata]), SEV_SIG)), BASIC_LIMIT)
    return np.where(ev, sev, 0.0)


def one_rep(scen, n_u, n_e, seed, B=1000):
    rng = np.random.default_rng(seed)
    w = draw_world(scen, rng); theta = true_theta(w); C = len(REL)
    us, ul, ucl = underwriting_pool(n_u, rng)
    obs = {}
    for c in range(C):
        loss = runs(w, c, us, ul, rng)
        obs[f"c{c}"] = [{"task_id": i, "stratum": STRATA[us[i]], "loss": float(loss[i]), "cluster": ucl[i]}
                        for i in range(len(us))]
    es = np.concatenate([np.full(k, i) for i, k in enumerate(allocation(W_DEPLOY, n_e).values())]).astype(int)
    el = rng.normal(0, SIGMA_U, len(es))
    R = np.zeros(C)
    for c in range(C):
        R[c] = (runs(w, c, es, el, rng, True).sum() + runs(w, c, es, el, rng, True).sum()) / (2 * len(es))
    res = {}
    for m in METHODS:
        f = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=0.5, method=m, B=B, seed=seed + 7)
        F = [f[f"c{c}"] for c in range(C)]; pts = np.array([x.point for x in F])
        res[m] = dict(
            cov_param=[bool(x.lo90 - 1e-12 <= theta[c] <= x.hi90 + 1e-12) for c, x in enumerate(F)],
            cov_pred=[bool(predictive_covered(x, R[c])) for c, x in enumerate(F)],
            cov_up95=[bool(R[c] <= x.pred_hi95 + 1e-12) for c, x in enumerate(F)],
            relbias=[float((x.point - theta[c]) / theta[c]) for c, x in enumerate(F)],
            iscore=[float(interval_score(x.pred_lo90, x.pred_hi90, R[c]) / theta[c]) for c, x in enumerate(F)],
            crps=[float(crps_samples(x.pred_draws, R[c]) / theta[c]) for c, x in enumerate(F)],
            pit=[randomized_pit(x.pred_draws, R[c], rng) for c, x in enumerate(F)],
            rel_width=[float((x.pred_hi90 - x.pred_lo90) / theta[c]) for c, x in enumerate(F)],
            spear=spearman(pts, R), conc=concordance(pts, R), faulty=[False] * C)
    return res


def _task(args):
    scen, n_u, n_e, rep = args
    return (scen, n_u, n_e), one_rep(scen, n_u, n_e, zlib.crc32(f"A3|{scen}|{n_u}|{n_e}".encode()) % 10_000_000 * 1000 + rep)


def summarise(reps):
    from scipy.stats import chisquare
    out = {}
    for m in METHODS:
        flat = lambda k: np.array([x for r in reps for x in r[m][k]], float)  # noqa: E731
        hist = np.histogram(flat("pit"), bins=10, range=(0, 1))[0]
        sp = np.array([r[m]["spear"] for r in reps], float); sp = sp[~np.isnan(sp)]
        out[m] = dict(cov_param=float(flat("cov_param").mean()), cov_pred=float(flat("cov_pred").mean()),
                      cov_up95=float(flat("cov_up95").mean()), relbias_mean=float(flat("relbias").mean()),
                      relbias_median=float(np.median(flat("relbias"))), iscore_rel=float(flat("iscore").mean()),
                      crps_rel=float(flat("crps").mean()), rel_width_median=float(np.median(flat("rel_width"))),
                      pit_hist=hist.tolist(), pit_maxdev=float(np.max(np.abs(hist / hist.sum() - 0.1))),
                      pit_chi2_p=float(chisquare(hist).pvalue),
                      spear_median=float(np.median(sp)), spear_p10=float(np.quantile(sp, 0.1)),
                      conc_median=float(np.nanmedian([r[m]["conc"] for r in reps])))
    return out


def main(out_path, reps=400, procs=7):
    grid = [(s, nu, ne) for s in SCEN for nu in (45, 90) for ne in (100, 200)]
    jobs = [(s, nu, ne, r) for (s, nu, ne) in grid for r in range(reps)]
    t0 = time.time(); acc = {g: [] for g in grid}
    with Pool(procs) as pool:
        for i, (g, r) in enumerate(pool.imap_unordered(_task, jobs, chunksize=4)):
            acc[g].append(r)
            if i % 1000 == 0:
                print(f"{i}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    json.dump({"reps": reps, "grid": {f"{s}|nu={nu}|ne={ne}": summarise(acc[(s, nu, ne)]) for (s, nu, ne) in grid},
               "design": {"U_COUNTS": U_COUNTS, "TEMPLATES": TEMPLATES, "BASE_RATE": BASE_RATE3.tolist(),
                          "TEMPLATE": [TEMPLATE_MU, TEMPLATE_SD], "SIGMA_SEV_CH": SIGMA_SEV_CH}},
              open(out_path, "w"), indent=1)
    print(f"done {time.time() - t0:.0f}s -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 400, int(sys.argv[3]) if len(sys.argv) > 3 else 7)
