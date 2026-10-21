"""Phase 0 v2 — technique validation after review 4 (pre-registered in EXPERIMENTS.md, Phase 0 v2).

Differences from simstudy.py (kept unchanged for reproducibility of the first grid):
  fixed stratified allocation (>=2 parents per stratum); PROP / NEYMAN (oracle + plug-in) / IS arms;
  realistic pre-run task-level control-variate score with an *estimated* pool mean and cross-fitted beta;
  Poisson near-miss counts with known / calibration-sample / misspecified R; zero-event upper bounds;
  mix misspecification arm; one-sided upper-bound coverage; runs AND parents needed for 1x1, 1x2, 5x2
  designs; latent ICC grid extended to 0.8-0.9 with observed ICC reported.
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np

from trustcurve.stats import icc_binary

W = np.array([0.35, 0.35, 0.20, 0.05, 0.05])
W_TRUE_SHIFT = np.array([0.30, 0.35, 0.20, 0.05, 0.10])     # mix-misspecification truth (5pt cancel->refusal)
IS_MIX = np.array([0.20, 0.20, 0.10, 0.20, 0.30])
BENCH = np.array([0.64, 0.28, 0.04, 0.02, 0.02])
LOGIT_SHIFT = np.log(np.array([1.0, 1.5, 0.8, 4.0, 8.0]))   # logit offsets (NOT relative risks)
SEV_SCALE = np.log(np.array([300, 400, 350, 250, 600]))
BASIC_LIMIT = 2000.0
R_NEAR = 10.0
Z90 = 1.6449
RESID = math.pi ** 2 / 3


def sig(x):
    return 1.0 / (1.0 + np.exp(-x))


class Cell:
    def __init__(self, q, icc, share):
        self.q, self.icc, self.share = q, icc, share
        tot = icc * RESID / (1 - icc)
        self.sP2, self.sV2 = tot * share, tot * (1 - share)
        g = np.random.default_rng(12345).standard_normal(200_000) * math.sqrt(tot)
        lo, hi = -20.0, 5.0
        for _ in range(60):
            mid = (lo + hi) / 2
            val = sum(W[h] * sig(mid + LOGIT_SHIFT[h] + g).mean() for h in range(5))
            lo, hi = (mid, hi) if val < q else (lo, mid)
        self.mu = (lo + hi) / 2 + LOGIT_SHIFT
        g2 = np.random.default_rng(999).standard_normal(400_000) * math.sqrt(tot)
        self.p_h = np.array([sig(self.mu[h] + g2).mean() for h in range(5)])
        self.sd_h = np.array([math.sqrt(max(self.p_h[h] * (1 - self.p_h[h]), 1e-12)) for h in range(5)])
        z = np.random.default_rng(11).standard_normal(400_000)
        self.lev_h = np.array([np.minimum(np.exp(SEV_SCALE[h] + 1.2 * z), BASIC_LIMIT).mean() for h in range(5)])
        self.truth = float(W @ self.p_h)
        self.truth_shift = float(W_TRUE_SHIFT @ self.p_h)
        self.truth_pp = float(W @ (self.p_h * self.lev_h))
        self.theta_sd = math.sqrt(self.sP2)

    def observed_icc(self, rng):
        """Observed-scale ICC of repeated runs of one task (variant), W-mixed, by simulation."""
        n = 20000
        h = rng.choice(5, size=n, p=W)
        th = self.mu[h] + rng.standard_normal(n) * math.sqrt(self.sP2 + self.sV2)
        y = (rng.random((n, 10)) < sig(th)[:, None]).astype(int)
        return icc_binary({str(i): list(y[i]) for i in range(n)})


def alloc(mix, n_par):
    k = np.maximum(2, np.round(mix * n_par)).astype(int)
    return np.repeat(np.arange(5), k)


def sample(cell: Cell, mix, n_runs, rng, variants=5, runs=2):
    per = variants * runs
    strat = alloc(mix, max(10, int(round(n_runs / per))))
    n_par = strat.size
    zp = rng.standard_normal(n_par)
    theta_p = cell.mu[strat] + zp * cell.theta_sd
    theta_v = np.repeat(theta_p, variants) + rng.standard_normal(n_par * variants) * math.sqrt(cell.sV2)
    p = sig(np.repeat(theta_v, runs))
    y = (rng.random(p.size) < p).astype(float)
    near = rng.poisson(R_NEAR * p).astype(float)
    h = np.repeat(strat, per)
    sev = np.minimum(np.exp(SEV_SCALE[h] + 1.2 * rng.standard_normal(p.size)), BASIC_LIMIT) * y
    par = np.repeat(np.arange(n_par), per)
    s_mix = np.bincount(strat, minlength=5) / n_par
    return dict(y=y, near=near, h=h, sev=sev, par=par, strat=strat, zp=zp, n_par=n_par, s_mix=s_mix)


def wmean_se(v, w, cl):
    sw = w.sum(); m = (w * v).sum() / sw
    z = np.bincount(cl, weights=w * (v - m)) / sw
    C = np.count_nonzero(np.bincount(cl))
    return m, math.sqrt(C / max(C - 1, 1) * float((z ** 2).sum()))


def wts(s, Wv=W):
    return (Wv / s["s_mix"])[s["h"]]


def interval(m, se, n_par):
    """Log-scale 90% two-sided; at m == 0 use CP one-sided 95% upper on n_eff = parents."""
    if m <= 0:
        return 0.0, 1 - 0.05 ** (1 / n_par)
    f = math.exp(Z90 * se / m)
    return m / f, m * f


def est_rate(s, Wv=W):
    return wmean_se(s["y"], wts(s, Wv), s["par"])


def score_task(cell, zp, r, offset, rng):
    return sig(offset + r * zp + math.sqrt(1 - r * r) * rng.standard_normal(zp.size))


def est_cv_realistic(s, cell, r, rng, pool=1000, offset=-1.5):
    sp = score_task(cell, s["zp"], r, offset, rng)
    x = sp[s["par"]]
    # pool mean of the pre-run score under W, estimated from an independent pool of task scores
    hp = rng.choice(5, size=pool, p=W)
    zpool = rng.standard_normal(pool)
    spool = score_task(cell, zpool, r, offset, rng)
    mu_x, var_mu = spool.mean(), spool.var(ddof=1) / pool
    w = wts(s)
    half = (s["par"] % 2 == 0)
    adj = np.empty_like(s["y"])
    for A, B in ((half, ~half), (~half, half)):  # cross-fit beta
        wa = w[A]; ya = s["y"][A]; xa = x[A]
        my = (wa * ya).sum() / wa.sum(); mx = (wa * xa).sum() / wa.sum()
        vx = (wa * (xa - mx) ** 2).sum() / wa.sum()
        beta = ((wa * (ya - my) * (xa - mx)).sum() / wa.sum()) / vx if vx > 0 else 0.0
        adj[B] = s["y"][B] - beta * (x[B] - mu_x)
    m, se = wmean_se(adj, w, s["par"])
    # add the pool-mean uncertainty (beta ~ overall slope)
    wa = w; my = (wa * s["y"]).sum() / wa.sum(); mx = (wa * x).sum() / wa.sum(); vx = (wa * (x - mx) ** 2).sum() / wa.sum()
    b = ((wa * (s["y"] - my) * (x - mx)).sum() / wa.sum()) / vx if vx > 0 else 0.0
    return m, math.sqrt(se * se + b * b * var_mu)


def est_near(s, R):
    m, se = wmean_se(s["near"], wts(s), s["par"])
    return m / R, se / R


def calib_R(cell, rng, n=2000):
    c = sample(cell, BENCH, n, rng)
    num = c["near"].sum(); den = c["y"].sum()
    if den == 0:
        return None, None
    Rh = num / den
    # cluster-robust delta-method variance of the ratio
    z = np.bincount(c["par"], weights=c["near"] - Rh * c["y"]) / den
    C = np.count_nonzero(np.bincount(c["par"]))
    return Rh, math.sqrt(C / (C - 1) * float((z ** 2).sum()))


def est_near_calib(s, Rh, seR):
    m, se = wmean_se(s["near"], wts(s), s["par"])
    p = m / Rh
    return p, p * math.sqrt((se / m) ** 2 + (seR / Rh) ** 2) if m > 0 else 0.0


def est_pp(s):
    return wmean_se(s["sev"], wts(s), s["par"])


def neyman_mix(sd):
    a = W * sd
    return a / a.sum()


def run_cell(cell: Cell, n_runs, reps, rng):
    arms = {}

    def rec(name, m, se, n_par, truth):
        lo, hi = interval(m, se, n_par)
        a = arms.setdefault(name, {"e": [], "c": [], "u": [], "hw": [], "zero": 0})
        a["e"].append(m); a["c"].append(lo <= truth <= hi); a["u"].append(truth <= hi); a["hw"].append((hi - lo) / 2)
        a["zero"] += (m <= 0)

    # plug-in Neyman from a 300-run pilot
    pil = sample(cell, W, 300, rng, 1, 1)
    sd_hat = np.array([max(pil["y"][pil["h"] == k].std(), 0.02) for k in range(5)])
    mixes = {"PROP": W, "NEYMAN_oracle": neyman_mix(cell.sd_h), "NEYMAN_plugin": neyman_mix(sd_hat), "IS": IS_MIX}
    Rh, seR = calib_R(cell, rng)
    for _ in range(reps):
        for k, mx in mixes.items():
            s = sample(cell, mx, n_runs, rng)
            m, se = est_rate(s); rec(f"T1_{k}", m, se, s["n_par"], cell.truth)
            if k == "PROP":
                rec("T1_PROP_mix_misspecified", m, se, s["n_par"], cell.truth_shift)
                rec("PP_capped_PROP", *est_pp(s), s["n_par"], cell.truth_pp)
                for r in (0.3, 0.6):
                    rec(f"T4r_r{r}_PROP", *est_cv_realistic(s, cell, r, rng), s["n_par"], cell.truth)
                rec("T3p_R_known", *est_near(s, R_NEAR), s["n_par"], cell.truth)
                rec("T3p_R_x1.5", *est_near(s, R_NEAR * 1.5), s["n_par"], cell.truth)
                if Rh:
                    rec("T3p_R_calibrated", *est_near_calib(s, Rh, seR), s["n_par"], cell.truth)
        for (v, r_) in ((1, 1), (1, 2)):  # designs for parents-needed
            s = sample(cell, W, n_runs, rng, v, r_)
            m, se = est_rate(s); rec(f"T1_PROP_design_{v}x{r_}", m, se, s["n_par"], cell.truth)
    out = {}
    for k, a in arms.items():
        tr = {"T1_PROP_mix_misspecified": cell.truth_shift, "PP_capped_PROP": cell.truth_pp}.get(k, cell.truth)
        e = np.array(a["e"]); rel_hw = float(np.mean(a["hw"]) / tr)
        per = {"design_1x1": 1, "design_1x2": 2}.get(k.replace("T1_PROP_", ""), 10)
        runs_need = int(n_runs * (rel_hw / 0.2) ** 2)
        out[k] = {"rel_bias": float(e.mean() / tr - 1), "cov90": float(np.mean(a["c"])), "upper95_cov": float(np.mean(a["u"])),
                  "rel_hw": rel_hw, "runs_for_pm20": runs_need, "parents_for_pm20": int(runs_need / per),
                  "zero_event_share": a["zero"] / reps}
    return out


def main(out_path, reps=300):
    rng = np.random.default_rng(20261021)
    grid = []
    for q in (0.005, 0.01, 0.02, 0.05):
        for icc in (0.1, 0.3, 0.6, 0.8, 0.9):
            for share in (0.5, 0.9):
                cell = Cell(q, icc, share)
                obs = cell.observed_icc(rng)
                for n in (500, 2000, 8000):
                    grid.append({"q": q, "latent_icc": icc, "observed_icc": round(obs, 3), "parent_share": share,
                                 "runs": n, "arms": run_cell(cell, n, reps, rng)})
                print(f"done q={q} icc={icc} share={share}", file=sys.stderr, flush=True)
    json.dump(grid, open(out_path, "w"), indent=1)


# --- credibility where it bites (T2f) ----------------------------------------------------------

def credibility_fine(reps=300, seed=7):
    """30 fine workflows, 2-8 parents each, 2 runs per parent. Target: each workflow's rate.
    Bühlmann–Straub with workflows as classes, parents as the observation units."""
    rng = np.random.default_rng(seed)
    out = []
    for between_sd in (0.3, 0.8):        # spread of workflow logit means
        for within_sd in (0.5, 1.5):     # spread of parent logits within a workflow
            mse_raw = []; mse_cred = []; cov = []
            for _ in range(reps):
                Wk = 30
                mu_w = -3.0 + rng.standard_normal(Wk) * between_sd
                npar = rng.integers(2, 9, size=Wk)
                truth = np.array([sig(mu_w[k] + rng.standard_normal(4000) * within_sd).mean() for k in range(Wk)])
                ys, ws = [], []
                for k in range(Wk):
                    th = mu_w[k] + rng.standard_normal(npar[k]) * within_sd
                    y = (rng.random((npar[k], 2)) < sig(th)[:, None]).astype(float)
                    ys.append(y); ws.append(k)
                runs = np.array([y.size for y in ys], float); tot = np.array([y.sum() for y in ys])
                raw = tot / runs
                grand = tot.sum() / runs.sum()
                # EPV: within-workflow variance of parent means (per run), VHM: between-workflow
                epv_num = sum(((y.mean(1) - y.mean()) ** 2).sum() * 2 for y in ys)
                epv_den = sum(y.shape[0] - 1 for y in ys)
                epv = max(epv_num / max(epv_den, 1), grand * (1 - grand) / 2)
                m = runs.sum()
                vhm = ((runs * (raw - grand) ** 2).sum() - (Wk - 1) * epv) / (m - (runs ** 2).sum() / m)
                vhm = max(vhm, 1e-8)
                Z = runs / (runs + epv / vhm)
                cred = Z * raw + (1 - Z) * grand
                # empirical-Bayes beta posterior interval for each workflow
                kap = max(grand * (1 - grand) / vhm - 1, 1.0)
                a0, b0 = grand * kap, (1 - grand) * kap
                from scipy.stats import beta as B
                lo = B.ppf(0.05, a0 + tot, b0 + runs - tot); hi = B.ppf(0.95, a0 + tot, b0 + runs - tot)
                mse_raw.append(((raw - truth) ** 2).mean()); mse_cred.append(((cred - truth) ** 2).mean())
                cov.append(((lo <= truth) & (truth <= hi)).mean())
            out.append({"between_sd": between_sd, "within_sd": within_sd,
                        "mse_ratio_cred_over_raw": float(np.mean(mse_cred) / np.mean(mse_raw)),
                        "eb_interval_cov90": float(np.mean(cov))})
    return out


if __name__ == "__main__":
    if sys.argv[1] == "fine":
        print(json.dumps(credibility_fine(), indent=1))
    else:
        main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 300)
