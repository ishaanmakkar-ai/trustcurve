"""Phase 0: validate pricing techniques on a simulated agent whose true loss rate is known.

Pre-registered in EXPERIMENTS.md (Phase 0). Everything here is offline and costs $0.

Model
  stratum h in STRATA; parent p in h: theta_p ~ N(mu_h, sP^2); variant v: theta_pv = theta_p + N(0, sV^2);
  run: loss ~ Bernoulli(sigmoid(theta_pv)); near-miss ~ Bernoulli(min(1, R * p_pv)) (R = 10);
  risk score X = sigmoid(theta_pv) + N(0, 0.05^2); severity ~ lognormal(scale_h, 1.2).
Truth = loss rate (and pure premium) under the ASSUMED real-world mix W, by large-sample integration.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass

import numpy as np

STRATA = ["cancel", "change", "book", "compensation", "refusal"]
W = np.array([0.35, 0.35, 0.20, 0.05, 0.05])            # assumed real-world mix (truth weights)
BENCH = np.array([0.64, 0.28, 0.04, 0.02, 0.02])        # benchmark-like sampling mix (tau2-ish)
IS_MIX = np.array([0.20, 0.20, 0.10, 0.20, 0.30])       # importance-sampling mix (oversample risky)
REL = np.array([1.0, 1.5, 0.8, 4.0, 8.0])               # relative risk by stratum (commission lives in refusal)
SEV_SCALE = np.log(np.array([300, 400, 350, 250, 600]))  # lognormal scale by stratum (USD)
R_NEAR = 10.0
Z90 = 1.6449
LOG_CI = True  # phase-0 loop 2: log-scale Wald intervals
LOGIT_RESID = math.pi ** 2 / 3


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class Scenario:
    q_target: float      # mixed loss rate under W
    icc: float           # latent-scale total ICC
    parent_share: float  # share of between-task variance at parent level
    seed: int = 0

    def variances(self):
        tot = self.icc * LOGIT_RESID / (1 - self.icc)
        return tot * self.parent_share, tot * (1 - self.parent_share)

    def mu(self, rng=None):
        """Stratum logit means so the W-mixed truth equals q_target (solved by bisection)."""
        sP2, sV2 = self.variances()
        g = np.random.default_rng(12345).standard_normal(200_000) * math.sqrt(sP2 + sV2)
        def mixed(off):
            return float(sum(W[h] * sigmoid(off + math.log(REL[h]) + g).mean() for h in range(5)))
        lo, hi = -15.0, 5.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if mixed(mid) < self.q_target else (lo, mid)
        off = (lo + hi) / 2
        return off + np.log(REL)

    def truth(self):
        sP2, sV2 = self.variances(); mu = self.mu()
        g = np.random.default_rng(999).standard_normal(400_000) * math.sqrt(sP2 + sV2)
        p_h = np.array([sigmoid(mu[h] + g).mean() for h in range(5)])
        sev_mean = np.exp(SEV_SCALE + 1.2 ** 2 / 2)
        noise = np.random.default_rng(7).standard_normal(g.size) * 0.05
        x_h = np.array([np.clip(sigmoid(mu[h] + g) + noise, 0, 1).mean() for h in range(5)])  # E[score], same noise+clip as runs
        z = np.random.default_rng(11).standard_normal(400_000)
        lev = np.array([np.minimum(np.exp(SEV_SCALE[h] + 1.2 * z), BASIC_LIMIT).mean() for h in range(5)])
        return {"rate": float(W @ p_h), "pure_premium": float(W @ (p_h * sev_mean)),
                "pure_premium_capped": float(W @ (p_h * lev)), "rate_h": p_h, "score_mean": float(W @ x_h)}


def draw_sample(sc: Scenario, mu, mix, n_runs, rng, variants=5, runs=2):
    """Parents allocated to strata by `mix`; each parent has `variants` variants x `runs` runs."""
    sP2, sV2 = sc.variances()
    per_parent = variants * runs
    n_par = max(len(STRATA), int(round(n_runs / per_parent)))
    strat = rng.choice(5, size=n_par, p=mix)
    theta_p = mu[strat] + rng.standard_normal(n_par) * math.sqrt(sP2)
    par = np.repeat(np.arange(n_par), per_parent)
    var_id = np.repeat(np.arange(n_par * variants), runs)
    theta_v = np.repeat(theta_p, variants) + rng.standard_normal(n_par * variants) * math.sqrt(sV2)
    p = sigmoid(np.repeat(theta_v, runs))
    y = (rng.random(p.size) < p).astype(float)
    near = (rng.random(p.size) < np.minimum(1, R_NEAR * p)).astype(float)
    x = np.clip(p + rng.standard_normal(p.size) * 0.05, 0, 1)
    h = np.repeat(strat, per_parent)
    sev = np.exp(SEV_SCALE[h] + 1.2 * rng.standard_normal(p.size)) * y
    return {"y": y, "near": near, "x": x, "h": h, "par": par, "var": var_id, "sev": sev, "mix": mix}


def _wmean_se(v, w, cl):
    """Self-normalised weighted mean with cluster-robust (linearised) SE."""
    sw = w.sum(); m = (w * v).sum() / sw
    z = np.bincount(cl, weights=w * (v - m)) / sw
    C = np.count_nonzero(np.bincount(cl))
    se = math.sqrt(C / max(C - 1, 1) * float((z ** 2).sum()))
    return m, se


def weights_for(s):
    return (W / s["mix"])[s["h"]]


def est_naive(s):
    return _wmean_se(s["y"], np.ones_like(s["y"]), s["par"])


def est_is(s, cluster="par"):
    return _wmean_se(s["y"], weights_for(s), s[cluster])


def est_is_pp(s):
    return _wmean_se(s["sev"], weights_for(s), s["par"])


BASIC_LIMIT = 2000.0  # USD per loss; phase-0 loop 3: price a capped basic limit (Palmer ILF practice)


def est_is_pp_capped(s, L=BASIC_LIMIT):
    return _wmean_se(np.minimum(s["sev"], L), weights_for(s), s["par"])


def est_near(s, R=R_NEAR):
    m, se = _wmean_se(s["near"], weights_for(s), s["par"])
    return m / R, se / R


def est_cv(s, mu_x):
    w = weights_for(s); sw = w.sum()
    my = (w * s["y"]).sum() / sw; mx = (w * s["x"]).sum() / sw
    cov = (w * (s["y"] - my) * (s["x"] - mx)).sum() / sw; vx = (w * (s["x"] - mx) ** 2).sum() / sw
    beta = cov / vx if vx > 0 else 0.0
    adj = s["y"] - beta * (s["x"] - mu_x)
    return _wmean_se(adj, w, s["par"])


def _buhlmann_point(y, h, par):
    """Bühlmann–Straub across strata (risk classes), observations = parent means, exposure = runs."""
    n_par = par.max() + 1
    py = np.bincount(par, weights=y, minlength=n_par); pn = np.bincount(par, minlength=n_par).astype(float)
    keep = pn > 0; py, pn = py[keep], pn[keep]
    ph = np.zeros(n_par, int); ph[par] = h; ph = ph[keep]
    pm = py / pn
    xbar = np.array([py[ph == k].sum() / max(pn[ph == k].sum(), 1) for k in range(5)])
    mk = np.array([pn[ph == k].sum() for k in range(5)])
    # EPV: within-stratum variance of parent means, exposure-weighted (parent is the unit)
    num = sum(((pn[ph == k]) * (pm[ph == k] - xbar[k]) ** 2).sum() for k in range(5))
    den = sum(max((ph == k).sum() - 1, 0) for k in range(5))
    epv = num / max(den, 1)
    m = mk.sum(); grand = (mk * xbar).sum() / m
    vhm = ((mk * (xbar - grand) ** 2).sum() - (np.count_nonzero(mk) - 1) * epv) / (m - (mk ** 2).sum() / m)
    vhm = max(vhm, 1e-9)
    K = epv / vhm
    Z = mk / (mk + K)
    # Complement must be mix-consistent: an IS sample's exposure-weighted grand mean is inflated by
    # the oversampled risky strata (found in phase-0 loop 1: +12% bias). Use the W-mixed stratum mean.
    complement = float(W @ xbar)
    cred = Z * xbar + (1 - Z) * complement
    return float(W @ cred)


def est_buhlmann(s, rng, B=200):
    pt = _buhlmann_point(s["y"], s["h"], s["par"])
    n_par = s["par"].max() + 1
    idx_by_par = np.split(np.arange(s["y"].size), np.cumsum(np.bincount(s["par"], minlength=n_par))[:-1])
    ph = np.zeros(n_par, int); ph[s["par"]] = s["h"]
    boots = []
    for _ in range(B):
        chosen = []
        for k in range(5):
            pk = np.flatnonzero(ph == k)
            if pk.size:
                chosen.append(rng.choice(pk, size=pk.size, replace=True))
        chosen = np.concatenate(chosen)
        rows = np.concatenate([idx_by_par[c] for c in chosen])
        newpar = np.repeat(np.arange(chosen.size), [idx_by_par[c].size for c in chosen])
        boots.append(_buhlmann_point(s["y"][rows], s["h"][rows], newpar))
    lo, hi = np.percentile(boots, [5, 95])
    return pt, (lo, hi)


def run_cell(sc: Scenario, n_runs: int, reps: int = 150, seed: int = 0):
    mu = sc.mu(); tr = sc.truth(); rng = np.random.default_rng(seed)
    out = {k: {"est": [], "cover": [], "hw": []} for k in
           ["T0_naive", "T0w_bench_reweighted", "T1_IS", "T1var_IS_variant_cluster", "T1pp_IS_pure_premium", "T1ppL_IS_pure_premium_capped",
            "T2_buhlmann", "T3_nearmiss_Rtrue", "T3_nearmiss_R_x1.5", "T4_control_variate"]}

    def rec(name, m, se=None, ci=None, truth=tr["rate"]):
        if ci is not None:
            lo, hi = ci
        elif LOG_CI and m > 0:  # log-scale interval (delta method): better for rare positive rates
            f = math.exp(Z90 * se / m); lo, hi = m / f, m * f
        else:
            lo, hi = (m - Z90 * se, m + Z90 * se)
        out[name]["est"].append(m); out[name]["cover"].append(lo <= truth <= hi); out[name]["hw"].append((hi - lo) / 2)

    for _ in range(reps):
        sb = draw_sample(sc, mu, BENCH, n_runs, rng)
        si = draw_sample(sc, mu, IS_MIX, n_runs, rng)
        rec("T0_naive", *est_naive(sb))
        rec("T0w_bench_reweighted", *est_is(sb))
        rec("T1_IS", *est_is(si))
        rec("T1var_IS_variant_cluster", *est_is(si, cluster="var"))
        rec("T1pp_IS_pure_premium", *est_is_pp(si), truth=tr["pure_premium"])
        rec("T1ppL_IS_pure_premium_capped", *est_is_pp_capped(si), truth=tr["pure_premium_capped"])
        pt, ci = est_buhlmann(si, rng); rec("T2_buhlmann", pt, ci=ci)
        rec("T3_nearmiss_Rtrue", *est_near(si))
        rec("T3_nearmiss_R_x1.5", *est_near(si, R=R_NEAR * 1.5))
        rec("T4_control_variate", *est_cv(si, tr["score_mean"]))

    res = {}
    for k, v in out.items():
        truth = {"T1pp_IS_pure_premium": tr["pure_premium"], "T1ppL_IS_pure_premium_capped": tr["pure_premium_capped"]}.get(k, tr["rate"])
        est = np.array(v["est"]); hw = np.array(v["hw"])
        rel_hw = float(np.mean(hw) / truth)
        res[k] = {"rel_bias": float(est.mean() / truth - 1), "coverage90": float(np.mean(v["cover"])),
                  "rel_halfwidth": rel_hw,
                  "runs_for_pm20pct": int(n_runs * (rel_hw / 0.20) ** 2) if rel_hw > 0 else None}
    return {"truth_rate": tr["rate"], "truth_pure_premium": tr["pure_premium"], "techniques": res}


def main(reps=150):
    grid = []
    for q in (0.02, 0.05):
        for icc in (0.1, 0.3, 0.6):
            for share in (0.5, 0.9):
                for n in (500, 2000, 8000):
                    sc = Scenario(q, icc, share)
                    r = run_cell(sc, n, reps=reps, seed=hash((q, icc, share, n)) % 2**31)
                    grid.append({"q": q, "icc_latent": icc, "parent_share": share, "runs": n, **r})
                    print(f"done q={q} icc={icc} share={share} n={n}", file=sys.stderr)
    return grid


if __name__ == "__main__":
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    res = main(reps)
    with open(sys.argv[1], "w") as f:
        json.dump(res, f, indent=1)
