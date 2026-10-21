"""Study 2 premium pipeline: underwriting observations -> pure-premium forecast + predictive interval.

The same code produces the phase-A simulated forecasts and the phase-C real (frozen) forecasts.

Input: for each configuration, a list of underwriting observations {"task_id", "stratum", "loss"}, where
``loss`` is the capped commission loss of one run (USD, 0 if no commission). Several runs of the same task
are collapsed to the task (tasks are the units).

Methods (STUDY2.md, phase A):
  M1       stratified task bootstrap, reweighted to the deployment mix W; pooled severity; zero-event
           Clopper-Pearson fallback.
  M2       frequency x severity. Frequency per (configuration, stratum) has a Beta prior centred on a
           multiplicative rating model m_h * r_c (stratum base x configuration relativity, Poisson-gamma
           credibility on r_c), with prior strength fitted across configurations (empirical Bayes,
           i.e. credibility blending across configurations). Severity is pooled across configurations.
  M2flat   M2 with a Jeffreys Beta(0.5, 0.5) prior per (configuration, stratum): no credibility.

Every method returns posterior/bootstrap draws of the pure premium theta and predictive draws of the
realised experience-period mean loss R, simulated for ``n_e`` new tasks x ``runs`` runs each with a
within-task run correlation ``rho``.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from scipy import stats as sps

STRATA = ("cancel", "change", "book", "compensation", "other")
W_DEPLOY = {"cancel": 0.30, "change": 0.30, "book": 0.15, "compensation": 0.15, "other": 0.10}
BASIC_LIMIT = 2000.0
FALLBACK_SEVERITY = (np.log(400.0), 1.0)
SPARSE_MIN = 5  # M1c: strata with fewer underwriting tasks use the configuration's pooled rate  # lognormal (mu, sigma) used only if no event exists anywhere


@dataclass
class Forecast:
    config: str
    method: str
    point: float
    lo90: float
    hi90: float
    pred_lo90: float
    pred_hi90: float
    pred_hi95: float
    n_tasks: int
    n_events: float
    freq_point: float
    theta_draws: np.ndarray = field(repr=False)
    pred_draws: np.ndarray = field(repr=False)
    notes: list = field(default_factory=list)

    def as_dict(self, n_keep: int = 0) -> dict:
        d = {k: getattr(self, k) for k in ("config", "method", "point", "lo90", "hi90", "pred_lo90",
                                            "pred_hi90", "pred_hi95", "n_tasks", "n_events", "freq_point", "notes")}
        d = {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in d.items()}
        if n_keep:
            idx = np.linspace(0, len(self.pred_draws) - 1, n_keep).astype(int)
            d["pred_draws"] = [round(float(x), 4) for x in np.sort(self.pred_draws)[idx]]
            d["theta_draws"] = [round(float(x), 4) for x in np.sort(self.theta_draws)[idx]]
        return d


def allocation(W: dict, n: int) -> dict:
    """Fixed allocation of n tasks to strata by largest remainder (the experience pool is built to W)."""
    raw = {h: W.get(h, 0.0) * n for h in STRATA}
    base = {h: int(math.floor(v)) for h, v in raw.items()}
    rest = n - sum(base.values())
    for h in sorted(STRATA, key=lambda h: raw[h] - base[h], reverse=True)[:rest]:
        base[h] += 1
    return base


def collapse(obs: list[dict], cap: float = BASIC_LIMIT):
    """-> {stratum: [(event_share, [event losses])]} with one entry per task."""
    by_task = defaultdict(list)
    for o in obs:
        by_task[(o["stratum"], str(o["task_id"]))].append(min(float(o["loss"]), cap))
    out = defaultdict(list)
    for (h, _), losses in by_task.items():
        ev = [x for x in losses if x > 1e-9]
        out[h].append((len(ev) / len(losses), ev))
    return out


def task_clusters(obs: list[dict], cap: float = BASIC_LIMIT):
    """-> {stratum: {cluster: (n_tasks, sum of task event shares)}}; cluster = obs["cluster"] or the task id."""
    by_task = defaultdict(list); clus = {}
    for o in obs:
        k = (o["stratum"], str(o["task_id"]))
        by_task[k].append(min(float(o["loss"]), cap))
        clus[k] = str(o.get("cluster") or o["task_id"])
    out = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    for (h, t), losses in by_task.items():
        c = out[h][clus[(h, t)]]
        c[0] += 1; c[1] += sum(x > 1e-9 for x in losses) / len(losses)
    return out


def _cluster_boot(cl: dict, B: int, rng) -> np.ndarray:
    """Cluster-bootstrap draws of a rate: resample clusters with replacement, rate = events / tasks."""
    n = np.array([v[0] for v in cl.values()], float); t = np.array([v[1] for v in cl.values()], float)
    idx = rng.integers(0, len(n), (B, len(n)))
    return t[idx].sum(1) / np.maximum(n[idx].sum(1), 1e-12)


def _severity_pool(collapsed_by_cfg):
    by_h, allv = defaultdict(list), []
    for col in collapsed_by_cfg.values():
        for h, tasks in col.items():
            for _, ev in tasks:
                by_h[h].extend(ev); allv.extend(ev)
    return by_h, allv


def _severity_draws(by_h, allv, B, rng, min_events=5):
    """Bayesian-bootstrap draws of mean severity per stratum, plus the support/weights for predictive draws."""
    out = {}
    for h in STRATA:
        vals = by_h.get(h, [])
        if len(vals) < min_events:
            vals = allv
        if len(vals) == 0:  # no event anywhere: labelled prior fallback
            mu, s = FALLBACK_SEVERITY
            sup = np.minimum(np.exp(rng.normal(mu, s, 400)), BASIC_LIMIT)
            wts = np.full((B, len(sup)), 1.0 / len(sup))
        else:
            sup = np.asarray(vals, float)
            wts = rng.dirichlet(np.ones(len(sup)), size=B)
        out[h] = (sup, wts, wts @ sup)
    return out


def _config_offsets(cols, by_h, allv, cfgs, B, rng, tau_floor=0.10, min_events=5):
    """Phase A loop 2: configuration-specific log-severity offsets (empirical-Bayes normal random effect).

    Residual = log(event loss) - mean log loss of the stratum's pooled severity support. tau (between-configuration
    SD) by method of moments, floored at ``tau_floor``; within-configuration variance pooled. Returns posterior
    draws of exp(offset) per configuration (B,), and the fitted (tau, sigma_w)."""
    ref = {}
    for h in STRATA:
        vals = by_h.get(h, [])
        vals = vals if len(vals) >= min_events else allv
        ref[h] = float(np.mean(np.log(vals))) if len(vals) else FALLBACK_SEVERITY[0]
    res = {c: [float(np.log(x)) - ref[h] for h, tasks in cols[c].items() for _, ev in tasks for x in ev if x > 0]
           for c in cfgs}
    within = [(r - np.mean(v)) ** 2 for v in res.values() if len(v) >= 2 for r in v]
    dfw = sum(len(v) - 1 for v in res.values() if len(v) >= 2)
    sw2 = max(float(np.sum(within) / dfw), 0.01) if dfw > 0 else 1.0  # floor: identical losses give 0 variance
    means = [(np.mean(v), len(v)) for v in res.values() if len(v) >= 1]
    if len(means) >= 3:
        m = np.array([x for x, _ in means]); n = np.array([k for _, k in means])
        tau2 = float(m.var(ddof=1) - np.mean(sw2 / n))
    else:
        tau2 = 0.0
    tau2 = max(tau2, tau_floor ** 2)
    out = {}
    for c in cfgs:
        v = res[c]
        if v:
            prec = 1 / tau2 + len(v) / sw2
            mu, var = (len(v) / sw2) * float(np.mean(v)) / prec, 1 / prec
        else:
            mu, var = 0.0, tau2
        out[c] = np.exp(rng.normal(mu, np.sqrt(var), B))
    return out, (float(np.sqrt(tau2)), float(np.sqrt(sw2)))


def _sum_severities(counts, sup, wts, rng, mult=None, cap=BASIC_LIMIT):
    """For each draw b, sum counts[b] severities drawn from support with weights wts[b] (x mult[b], re-capped)."""
    B = len(counts); tot = np.zeros(B)
    nz = np.nonzero(counts)[0]
    if len(nz) == 0:
        return tot
    cdf = np.cumsum(wts[nz], axis=1)
    k = counts[nz]
    rows = np.repeat(np.arange(len(nz)), k)
    u = rng.random(len(rows))
    idx = (cdf[rows] < u[:, None]).sum(axis=1)
    idx = np.minimum(idx, len(sup) - 1)
    vals = sup[idx] if mult is None else np.minimum(sup[idx] * mult[nz][rows], cap)
    tot[nz] = np.bincount(rows, weights=vals, minlength=len(nz))
    return tot


def _predictive(p_draws: dict, sev: dict, n_alloc: dict, runs: int, rho: float, rng, mult=None) -> np.ndarray:
    """Simulate the realised mean loss per run over the experience period for each draw."""
    B = len(next(iter(p_draws.values())))
    total = np.zeros(B); n_runs = 0
    for h in STRATA:
        n = n_alloc.get(h, 0)
        if n == 0:
            continue
        p = np.clip(p_draws[h], 0.0, 1.0)
        if runs == 1:
            ev = rng.binomial(n, p)
        else:
            # beta-binomial events per task with intra-task correlation rho: Beta(a, b), a+b = (1-rho)/rho
            if rho <= 0:
                ev = rng.binomial(n * runs, p)
            else:
                s = (1 - rho) / rho
                a = np.maximum(p * s, 1e-9); b = np.maximum((1 - p) * s, 1e-9)
                pt = rng.beta(a[:, None].repeat(n, 1), b[:, None].repeat(n, 1))
                ev = rng.binomial(runs, pt).sum(axis=1)
        sup, wts, _ = sev[h]
        total += _sum_severities(ev, sup, wts, rng, mult)
        n_runs += n * runs
    return total / max(n_runs, 1)


def _stratum_counts(col):
    return {h: (len(col.get(h, [])), float(sum(e for e, _ in col.get(h, [])))) for h in STRATA}


def forecast(obs_by_cfg: dict[str, list[dict]], W: dict | None = None, n_e: int | dict = 200, runs: int = 2,
             rho: float = 0.5, method: str = "M2", B: int = 1000, seed: int = 0,
             cap: float = BASIC_LIMIT, prior_cap: float = 200.0, exp_alloc: dict | None = None,
             config_severity: bool = True) -> dict[str, Forecast]:
    W = W or W_DEPLOY
    rng = np.random.default_rng(seed)
    cols = {c: collapse(o, cap) for c, o in obs_by_cfg.items()}
    counts = {c: _stratum_counts(col) for c, col in cols.items()}
    by_h, allv = _severity_pool(cols)
    sev = _severity_draws(by_h, allv, B, rng)
    n_alloc_of = (lambda c: exp_alloc or allocation(W, n_e[c] if isinstance(n_e, dict) else n_e))
    cfgs = list(obs_by_cfg)
    mults, sev_fit = _config_offsets(cols, by_h, allv, cfgs, B, rng) if config_severity else ({}, None)

    # pooled stratum base rates m_h (shared across configurations)
    N_h = {h: sum(counts[c][h][0] for c in cfgs) for h in STRATA}
    X_h = {h: sum(counts[c][h][1] for c in cfgs) for h in STRATA}
    N_all, X_all = sum(N_h.values()), sum(X_h.values())
    m_hat = {h: (X_h[h] + 0.5) / (N_h[h] + 1.0) if N_h[h] else (X_all + 0.5) / (N_all + 1.0) for h in STRATA}

    if method == "M2":
        # configuration relativity r_c: Poisson-gamma credibility, k by method of moments across configurations
        E = {c: sum(counts[c][h][0] * m_hat[h] for h in STRATA) for c in cfgs}
        X = {c: sum(counts[c][h][1] for h in STRATA) for c in cfgs}
        ratios = np.array([X[c] / E[c] for c in cfgs if E[c] > 0])
        Ebar = np.mean([E[c] for c in cfgs if E[c] > 0]) if ratios.size else 1.0
        var_between = ratios.var(ddof=1) - (ratios.mean() / Ebar) if ratios.size > 1 else 0.0
        k = (ratios.mean() ** 2 / var_between) if var_between > 1e-12 else 1e6
        k = float(np.clip(k, 0.5, 1e6))
        # stratum prior strength M_h from residual dispersion of (c,h) rates around m_h * r_c
        r_hat = {c: (k + X[c]) / (k + E[c]) for c in cfgs}
        M_h = {}
        for h in STRATA:
            res, vb = [], []
            for c in cfgs:
                n, x = counts[c][h]
                if n >= 2:
                    pi = min(m_hat[h] * r_hat[c], 0.99)
                    res.append((x / n - pi) ** 2); vb.append(pi * (1 - pi) / n)
            if len(res) >= 3:
                excess = np.mean(res) - np.mean(vb)
                pbar = m_hat[h]
                M_h[h] = float(np.clip(pbar * (1 - pbar) / excess - 1, 2.0, prior_cap)) if excess > 1e-12 else prior_cap
            else:
                M_h[h] = prior_cap
        m_draw = {h: rng.gamma(X_h[h] + 0.5, 1.0, B) / (N_h[h] + 1.0) if N_h[h] else
                  rng.gamma(X_all + 0.5, 1.0, B) / (N_all + 1.0) * rng.lognormal(0, 0.5, B) for h in STRATA}

    out = {}
    for c in cfgs:
        notes = []
        p_draws = {}
        if method == "M2":
            r_draw = rng.gamma(k + X[c], 1.0, B) / (k + E[c])
            for h in STRATA:
                n, x = counts[c][h]
                pi = np.clip(m_draw[h] * r_draw, 1e-6, 0.99)
                M = M_h[h]
                p_draws[h] = rng.beta(M * pi + x, M * (1 - pi) + n - x)
            notes.append(f"k={k:.3g}; Z={E[c] / (E[c] + k):.2f}")
        elif method == "M2flat":
            for h in STRATA:
                n, x = counts[c][h]
                p_draws[h] = rng.beta(0.5 + x, 0.5 + n - x, B)
                if n == 0:
                    notes.append(f"no tasks in {h}: Jeffreys prior only")
        elif method == "M1c":  # phase-A loop 3 (review 6 #2, #8): cluster bootstrap + sparse-stratum pooling
            tc = task_clusters(obs_by_cfg[c], cap)
            allcl = {f"{h}|{k}": v for h, d in tc.items() for k, v in d.items()}
            pooled = _cluster_boot(allcl, B, rng) if allcl else np.zeros(B)
            for h in STRATA:
                n_h = sum(v[0] for v in tc.get(h, {}).values())
                if n_h >= SPARSE_MIN:
                    p_draws[h] = _cluster_boot(tc[h], B, rng)
                else:
                    p_draws[h] = pooled; notes.append(f"{h}: {n_h} tasks < {SPARSE_MIN}, pooled rate")
        elif method == "M1":
            col = cols[c]
            n_c = sum(counts[c][h][0] for h in STRATA)
            pooled = np.array([e for h in STRATA for e, _ in col.get(h, [])])
            for h in STRATA:
                e = np.array([e for e, _ in col.get(h, [])])
                if len(e) == 0:
                    e = pooled; notes.append(f"no tasks in {h}: config pooled rate")
                idx = rng.integers(0, len(e), size=(B, len(e)))
                p_draws[h] = e[idx].mean(axis=1)
        else:
            raise ValueError(method)

        mult = mults.get(c)
        if mult is None:
            sev_c = {h: sev[h][2] for h in STRATA}
        else:
            sev_c = {h: (sev[h][1] * np.minimum(sev[h][0][None, :] * mult[:, None], cap)).sum(axis=1) for h in STRATA}
            notes.append(f"severity offset x{np.median(mult):.2f} (tau={sev_fit[0]:.2f})")
        theta = sum(W.get(h, 0.0) * p_draws[h] * sev_c[h] for h in STRATA)
        pred = _predictive(p_draws, sev, n_alloc_of(c), runs, rho, rng, mult)
        n_tasks = sum(counts[c][h][0] for h in STRATA)
        n_ev = sum(counts[c][h][1] for h in STRATA)
        sev_mean = {h: float(sev_c[h].mean()) for h in STRATA}
        hi90 = float(np.quantile(theta, 0.95)); pred_hi = float(np.quantile(pred, 0.95)); pred_hi95 = pred_hi
        if method in ("M1", "M1c"):
            col = cols[c]
            pooled_rate = n_ev / max(n_tasks, 1)
            thin = (lambda h: len(col.get(h, [])) < SPARSE_MIN) if method == "M1c" else (lambda h: not col.get(h))
            point = float(sum(W.get(h, 0.0) * (pooled_rate if thin(h) else np.mean([e for e, _ in col[h]]))
                              * sev_mean[h] for h in STRATA))
            if n_ev == 0:  # zero-event fallback: CP 95% upper on tasks x pooled mean severity
                ub = (1 - 0.05 ** (1 / max(n_tasks, 1))) * float(np.mean(list(sev_mean.values())))
                hi90 = max(hi90, ub); pred_hi = max(pred_hi, ub); pred_hi95 = pred_hi
                notes.append("zero events: CP fallback upper")
        else:
            point = float(np.mean(theta))
        freq = float(sum(W.get(h, 0.0) * p_draws[h].mean() for h in STRATA))
        out[c] = Forecast(config=c, method=method, point=point, lo90=float(np.quantile(theta, 0.05)), hi90=hi90,
                          pred_lo90=float(np.quantile(pred, 0.05)), pred_hi90=pred_hi,
                          pred_hi95=pred_hi95,
                          n_tasks=n_tasks, n_events=n_ev, freq_point=freq, theta_draws=theta, pred_draws=pred,
                          notes=notes)
    return out


# --- scoring (used in phase A and phase C) ----------------------------------------------------------------

def interval_score(lo, hi, y, alpha=0.1):
    return (hi - lo) + (2 / alpha) * max(lo - y, 0.0) + (2 / alpha) * max(y - hi, 0.0)


def crps_samples(draws: np.ndarray, y: float) -> float:
    x = np.sort(np.asarray(draws, float)); n = len(x)
    term1 = np.mean(np.abs(x - y))
    # E|X - X'| via sorted formula
    i = np.arange(1, n + 1)
    term2 = 2 * np.sum((2 * i - n - 1) * x) / (n * n)
    return float(term1 - 0.5 * term2)


def randomized_pit(draws: np.ndarray, y: float, rng) -> float:
    d = np.asarray(draws)
    lo = np.mean(d < y - 1e-12); hi = np.mean(d <= y + 1e-12)
    return float(lo + rng.random() * (hi - lo))


def predictive_covered(f: Forecast, y: float) -> bool:
    return f.pred_lo90 - 1e-9 <= y <= f.pred_hi90 + 1e-9


def spearman(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    return float(sps.spearmanr(a, b).statistic)


def concordance(a, b) -> float:
    """Share of configuration pairs ordered the same way (ties in either count as 0.5)."""
    a, b = np.asarray(a, float), np.asarray(b, float); s = 0.0; n = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            n += 1
            da, db = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
            s += 0.5 if (da == 0 or db == 0) else float(da == db)
    return s / n if n else float("nan")
