"""Study 2 B5 power analysis: phase-A machinery re-parameterised with the screening (underwriting) rates.

Truth for each configuration = its screening estimate per stratum (Jeffreys-smoothed frequency; pooled event
severities, lognormal fallback), with shared latent task difficulty (sigma_u = 1.0, as phase A) and optionally an
author shift between underwriting and experience pools (phase-A S2, delta_h ~ N(0, 0.5^2)).
For a candidate design {config: (n_u, n_e)} it simulates underwriting + experience, forecasts with M1 (the frozen
primary) and reports median / p10 Spearman, predictive coverage (all configs and configs with >=1 realised event),
sharpness and the expected number of zero-event configurations.

Usage: python -m trustcurve.study2.power <screen_runs.csv> [...] --design design.json --out power.json
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict

import numpy as np
from scipy.optimize import brentq

from trustcurve.study2.forecast import (BASIC_LIMIT, STRATA, W_DEPLOY, allocation, forecast, spearman)

SIGMA_U = 1.0
GH_X, GH_W = np.polynomial.hermite_e.hermegauss(40)
GH_W = GH_W / GH_W.sum()


def _sig(x):
    return 1 / (1 + np.exp(-x))


def _intercept(p):
    """Latent intercept a with E_u[sigmoid(a + u)] = p, u ~ N(0, SIGMA_U^2)."""
    p = min(max(p, 1e-5), 0.95)
    return brentq(lambda a: float(np.sum(GH_W * _sig(a + SIGMA_U * GH_X))) - p, -25, 10)


def estimate_truth(rows, pseudo=0.5):
    """{config: {stratum: p}} from screening rows by a multiplicative rating model: pooled stratum base rate m_h
    (all configurations; empty strata get the overall rate) x configuration relativity r_c = (X_c + pseudo) /
    (E_c + pseudo). Per-stratum Jeffreys was rejected: thin or empty strata (book 2, other 0 tasks) got 17-50%.
    Also returns the pooled event severities."""
    n = defaultdict(lambda: defaultdict(int)); x = defaultdict(lambda: defaultdict(float)); sev = []
    for r in rows:
        c, h = r["config"], r["stratum"]
        loss = float(r["commission_usd"] or 0)
        n[c][h] += 1; x[c][h] += loss > 0
        if loss > 0:
            sev.append(min(loss, BASIC_LIMIT))
    N = {h: sum(n[c][h] for c in n) for h in STRATA}; X = {h: sum(x[c][h] for c in n) for h in STRATA}
    overall = (sum(X.values()) + pseudo) / (sum(N.values()) + 1)
    m = {h: (X[h] + pseudo * overall * 10) / (N[h] + 10) if N[h] else overall for h in STRATA}
    truth = {}
    for c in n:
        E = sum(n[c][h] * m[h] for h in STRATA); Xc = sum(x[c][h] for h in STRATA)
        r_c = (Xc + pseudo) / (E + pseudo)
        truth[c] = {h: min(m[h] * r_c, 0.9) for h in STRATA}
    return truth, (np.array(sev) if sev else None)


def simulate(truth, sev, design, reps=200, shift=0.0, seed=0, U_mix=None):
    rng = np.random.default_rng(seed)
    cfgs = sorted(design)
    A = {c: {h: _intercept(truth[c][h]) for h in STRATA} for c in cfgs}
    if sev is None or len(sev) < 3:
        sev_draw = lambda k: np.minimum(np.exp(rng.normal(np.log(300), 1.0, k)), BASIC_LIMIT)  # noqa: E731
    else:
        sev_draw = lambda k: rng.choice(sev, k)  # noqa: E731
    U_mix = U_mix or {"cancel": 0.50, "change": 0.26, "book": 0.03, "compensation": 0.20, "other": 0.01}
    out = []
    for _ in range(reps):
        delta = rng.normal(0, shift, len(STRATA)) if shift else np.zeros(len(STRATA))
        nu_max = max(d[0] for d in design.values()); ne_max = max(d[1] for d in design.values())
        us = np.concatenate([np.full(k, i) for i, k in enumerate(allocation(U_mix, nu_max).values())])
        es = np.concatenate([np.full(k, i) for i, k in enumerate(allocation(W_DEPLOY, ne_max).values())])
        uu, eu = rng.normal(0, SIGMA_U, len(us)), rng.normal(0, SIGMA_U, len(es))
        rng.shuffle(perm_u := np.arange(len(us))); rng.shuffle(perm_e := np.arange(len(es)))
        obs, R, Rev = {}, {}, {}
        for c in cfgs:
            nu, ne = design[c]
            iu = perm_u[:nu]; ie = perm_e[:ne]
            a = np.array([A[c][STRATA[h]] for h in us[iu]])
            ev = rng.random(nu) < _sig(a + uu[iu])
            loss = np.where(ev, sev_draw(nu), 0.0)
            obs[c] = [{"task_id": int(i), "stratum": STRATA[us[i]], "loss": float(l)} for i, l in zip(iu, loss)]
            ae = np.array([A[c][STRATA[h]] + delta[h] for h in es[ie]])
            tot, k = 0.0, 0
            for _s in range(2):
                e2 = rng.random(ne) < _sig(ae + eu[ie])
                tot += float(np.where(e2, sev_draw(ne), 0.0).sum()); k += int(e2.sum())
            R[c] = tot / (2 * ne); Rev[c] = k
        f = forecast(obs, n_e={c: design[c][1] for c in cfgs}, method="M1", B=400, seed=int(rng.integers(1e9)))
        pts = np.array([f[c].point for c in cfgs]); ys = np.array([R[c] for c in cfgs])
        cov = [f[c].pred_lo90 - 1e-9 <= R[c] <= f[c].pred_hi90 + 1e-9 for c in cfgs]
        cov_ev = [cv for cv, c in zip(cov, cfgs) if Rev[c] > 0]
        out.append(dict(spear=spearman(pts, ys), cov=float(np.mean(cov)),
                        cov_ev=float(np.mean(cov_ev)) if cov_ev else np.nan, zero=sum(Rev[c] == 0 for c in cfgs),
                        width=float(np.median([(f[c].pred_hi90 - f[c].pred_lo90) / max(f[c].point, 1e-6) for c in cfgs]))))
    sp = np.array([o["spear"] for o in out], float); sp = sp[~np.isnan(sp)]
    return {"reps": reps, "shift": shift, "spearman_median": float(np.median(sp)) if sp.size else None,
            "spearman_p10": float(np.quantile(sp, 0.1)) if sp.size else None,
            "p_spearman_le_0.3": float(np.mean(sp <= 0.3)) if sp.size else None,
            "coverage_mean": float(np.mean([o["cov"] for o in out])),
            "coverage_event_configs_mean": float(np.nanmean([o["cov_ev"] for o in out])),
            "zero_event_configs_mean": float(np.mean([o["zero"] for o in out])),
            "median_relative_width": float(np.median([o["width"] for o in out]))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+"); ap.add_argument("--design", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=200)
    a = ap.parse_args()
    rows = [r for p in a.runs for r in csv.DictReader(open(p)) if not r.get("error")]
    truth, sev = estimate_truth(rows)
    designs = json.load(open(a.design))
    res = {"truth_freq_under_W": {c: sum(W_DEPLOY[h] * p for h, p in t.items()) for c, t in truth.items()},
           "n_severity_events": 0 if sev is None else int(len(sev)), "designs": {}}
    for name, d in designs.items():
        d = {c: tuple(v) for c, v in d.items() if c in truth}
        res["designs"][name] = {s: simulate(truth, sev, d, a.reps, shift=s, seed=7) for s in (0.0, 0.5)}
        print(name, json.dumps(res["designs"][name]))
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
