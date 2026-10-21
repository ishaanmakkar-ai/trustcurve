"""Study 2 phase A: known-truth ADEMP simulation of the full premium pipeline (pre-registered in STUDY2.md §A).

Each replication: draw 12 configurations' true parameters, an underwriting pool and an experience pool
(tasks shared by all configurations, as in the real study), simulate underwriting runs (1 per task) and
experience runs (n_e tasks x 2 simulators), forecast with forecast.py, and score against the known truth.

Usage: python -m trustcurve.study2.sim_a <out.json> [reps] [procs]
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

H = len(STRATA)
W = np.array([W_DEPLOY[h] for h in STRATA])
U_MIX = {"cancel": 0.45, "change": 0.25, "book": 0.05, "compensation": 0.15, "other": 0.10}
W_WRONG = {"cancel": 0.30, "change": 0.20, "book": 0.15, "compensation": 0.25, "other": 0.10}  # S1 truth
BASE_RATE = np.array([0.02, 0.01, 0.005, 0.04, 0.005])     # base configuration, median task
SEV_MED = np.array([400.0, 300.0, 500.0, 200.0, 300.0]); SEV_SIG = 1.0
REL = np.array([0.5, 1, 1, 1.3, 1.7, 2.2, 3, 4, 6, 9, 14, 20.0])
SIGMA_U, SIGMA_G, SIGMA_B, SIGMA_SEVC = 1.0, 0.3, 0.2, 0.2
SCEN = ("S0", "S1", "S2", "S3", "S4", "S5")
METHODS = ("M1", "M2", "M2flat")
GH_X, GH_W = np.polynomial.hermite_e.hermegauss(40)
GH_W = GH_W / GH_W.sum()


def logit(p):
    return np.log(p / (1 - p))


def sig(x):
    return 1 / (1 + np.exp(-x))


def capped_lognormal_mean(med, s, L=BASIC_LIMIT):
    from scipy.stats import norm
    mu = np.log(med)
    z = (np.log(L) - mu) / s
    return np.exp(mu + s * s / 2) * norm.cdf(z - s) + L * (1 - norm.cdf(z))


def draw_world(scen, rng):
    C = len(REL)
    alpha = logit(BASE_RATE * (0.25 if scen == "S5" else 1.0))
    beta = np.log(REL) + rng.normal(0, SIGMA_B, C)
    gamma = rng.normal(0, SIGMA_G, (C, H))
    sevc = np.exp(rng.normal(0, SIGMA_SEVC, C))
    delta = rng.normal(0, 0.5, H) if scen == "S2" else np.zeros(H)
    sim2 = rng.normal(0, 0.4, C) if scen == "S3" else np.zeros(C)
    faulty = rng.choice(C, 2, replace=False) if scen == "S4" else np.array([], int)
    return dict(alpha=alpha, beta=beta, gamma=gamma, sevc=sevc, delta=delta, sim2=sim2, faulty=faulty)


def true_theta(w, Wtrue, scen):
    """theta_c: expected capped loss per run in the experience period (2 simulators averaged)."""
    C = len(REL); th = np.zeros(C)
    for c in range(C):
        tot = 0.0
        for h in range(H):
            base = w["alpha"][h] + w["beta"][c] + w["gamma"][c, h] + w["delta"][h]
            sevm = capped_lognormal_mean(SEV_MED[h] * w["sevc"][c], SEV_SIG)
            ps = []
            for shift in (0.0, w["sim2"][c]):
                p_norm = np.sum(GH_W * sig(base + shift + SIGMA_U * GH_X))
                if c in w["faulty"]:
                    p_f = np.sum(GH_W * sig(base + shift + 2.5 + SIGMA_U * GH_X))
                    p_norm = 0.9 * p_norm + 0.1 * p_f
                ps.append(p_norm)
            tot += Wtrue[h] * np.mean(ps) * sevm
        th[c] = tot
    return th


def sim_runs(w, c, strata_idx, u, rng, shift=0.0, delta=None, subtype=None):
    lg = (w["alpha"][strata_idx] + w["beta"][c] + w["gamma"][c, strata_idx] + u + shift
          + (delta[strata_idx] if delta is not None else 0.0))
    if subtype is not None and c in w["faulty"]:
        lg = lg + 2.5 * subtype
    ev = rng.random(len(lg)) < sig(lg)
    sev = np.minimum(np.exp(rng.normal(np.log(SEV_MED[strata_idx] * w["sevc"][c]), SEV_SIG)), BASIC_LIMIT)
    return np.where(ev, sev, 0.0)


def strata_vector(alloc):
    return np.concatenate([np.full(alloc[h], i) for i, h in enumerate(STRATA)]).astype(int)


def one_rep(scen, n_u, n_e, seed, B=1000):
    rng = np.random.default_rng(seed)
    w = draw_world(scen, rng)
    Wtrue_d = W_WRONG if scen == "S1" else W_DEPLOY
    Wtrue = np.array([Wtrue_d[h] for h in STRATA])
    theta = true_theta(w, Wtrue, scen)
    C = len(REL)
    # underwriting: shared tasks, 1 run per configuration
    us = strata_vector(allocation(U_MIX, n_u)); uu = rng.normal(0, SIGMA_U, len(us))
    obs = {}
    for c in range(C):
        loss = sim_runs(w, c, us, uu, rng)
        obs[f"c{c}"] = [{"task_id": i, "stratum": STRATA[us[i]], "loss": float(loss[i])} for i in range(len(us))]
    # experience: n_e new tasks at the true mix, 2 simulators
    es = strata_vector(allocation(Wtrue_d, n_e)); eu = rng.normal(0, SIGMA_U, len(es))
    sub = (rng.random(len(es)) < 0.10).astype(float) if scen == "S4" else None
    R = np.zeros(C)
    for c in range(C):
        l1 = sim_runs(w, c, es, eu, rng, 0.0, w["delta"], sub)
        l2 = sim_runs(w, c, es, eu, rng, w["sim2"][c], w["delta"], sub)
        R[c] = (l1.sum() + l2.sum()) / (2 * len(es))
    res = {}
    for m in METHODS:
        f = forecast(obs, W_DEPLOY, n_e=n_e, runs=2, rho=0.5, method=m, B=B, seed=seed + 7)
        F = [f[f"c{c}"] for c in range(C)]
        pts = np.array([x.point for x in F])
        res[m] = dict(
            cov_param=[bool(x.lo90 - 1e-12 <= theta[c] <= x.hi90 + 1e-12) for c, x in enumerate(F)],
            cov_pred=[bool(predictive_covered(x, R[c])) for c, x in enumerate(F)],
            cov_up95=[bool(R[c] <= x.pred_hi95 + 1e-12) for c, x in enumerate(F)],
            relbias=[float((x.point - theta[c]) / theta[c]) for c, x in enumerate(F)],
            iscore=[float(interval_score(x.pred_lo90, x.pred_hi90, R[c]) / theta[c]) for c, x in enumerate(F)],
            crps=[float(crps_samples(x.pred_draws, R[c]) / theta[c]) for c, x in enumerate(F)],
            pit=[randomized_pit(x.pred_draws, R[c], rng) for c, x in enumerate(F)],
            rel_width=[float((x.pred_hi90 - x.pred_lo90) / theta[c]) for c, x in enumerate(F)],
            spear=spearman(pts, R), spear_truth=spearman(pts, theta), conc=concordance(pts, R),
            faulty=[bool(c in w["faulty"]) for c in range(C)],
        )
    res["spear_R_theta"] = spearman(R, theta)
    return res


def _task(args):
    scen, n_u, n_e, rep = args
    seed = zlib.crc32(f"{scen}|{n_u}|{n_e}".encode()) % 10_000_000 * 1000 + rep
    return (scen, n_u, n_e), one_rep(scen, n_u, n_e, seed)


def summarise(reps):
    out = {}
    for m in METHODS:
        def flat(k):
            return np.array([x for r in reps for x in r[m][k]], float)
        cp = flat("cov_pred"); per_rep = np.array([np.mean(r[m]["cov_pred"]) for r in reps])
        pit = flat("pit"); hist = np.histogram(pit, bins=10, range=(0, 1))[0]
        from scipy.stats import chisquare
        sp = np.array([r[m]["spear"] for r in reps], float); sp = sp[~np.isnan(sp)]
        fa = np.array([x for r in reps for x in r[m]["faulty"]], bool)
        d = dict(
            cov_param=float(flat("cov_param").mean()), cov_pred=float(cp.mean()),
            cov_pred_se=float(per_rep.std(ddof=1) / np.sqrt(len(reps))),
            cov_up95=float(flat("cov_up95").mean()),
            relbias_mean=float(flat("relbias").mean()), relbias_median=float(np.median(flat("relbias"))),
            iscore_rel=float(flat("iscore").mean()), crps_rel=float(flat("crps").mean()),
            rel_width_median=float(np.median(flat("rel_width"))),
            pit_hist=hist.tolist(), pit_chi2_p=float(chisquare(hist).pvalue),
            pit_maxdev=float(np.max(np.abs(hist / hist.sum() - 0.1))),
            spear_median=float(np.median(sp)) if sp.size else None,
            spear_p10=float(np.quantile(sp, 0.10)) if sp.size else None,
            spear_truth_median=float(np.nanmedian([r[m]["spear_truth"] for r in reps])),
            conc_median=float(np.nanmedian([r[m]["conc"] for r in reps])),
        )
        if fa.any():
            d["cov_pred_faulty"] = float(cp[fa].mean()); d["cov_pred_nonfaulty"] = float(cp[~fa].mean())
        out[m] = d
    out["spear_R_theta_median"] = float(np.nanmedian([r["spear_R_theta"] for r in reps]))
    return out


def main(out_path, reps=400, procs=6):
    grid = [(s, nu, ne) for s in SCEN for nu in (45, 90, 180) for ne in (100, 200)]
    jobs = [(s, nu, ne, r) for (s, nu, ne) in grid for r in range(reps)]
    t0 = time.time(); acc = {g: [] for g in grid}
    with Pool(procs) as pool:
        for i, (g, r) in enumerate(pool.imap_unordered(_task, jobs, chunksize=4)):
            acc[g].append(r)
            if i % 2000 == 0:
                print(f"{i}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    summary = {f"{s}|nu={nu}|ne={ne}": summarise(acc[(s, nu, ne)]) for (s, nu, ne) in grid}
    json.dump({"reps": reps, "grid": summary, "design": {
        "U_MIX": U_MIX, "W": W_DEPLOY, "W_WRONG_S1": W_WRONG, "BASE_RATE": BASE_RATE.tolist(),
        "REL": REL.tolist(), "SEV_MED": SEV_MED.tolist(), "SEV_SIG": SEV_SIG, "SIGMA_U": SIGMA_U,
        "SIGMA_G": SIGMA_G, "SIGMA_B": SIGMA_B, "SIGMA_SEVC": SIGMA_SEVC, "rho_assumed": 0.5}},
        open(out_path, "w"), indent=1)
    print(f"done {time.time() - t0:.0f}s -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 400, int(sys.argv[3]) if len(sys.argv) > 3 else 6)
