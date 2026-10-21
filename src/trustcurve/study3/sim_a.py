"""Study 3 phase A': known-truth simulation of the three-forecaster comparison (pre-registered in STUDY3.md §A').

Each replication draws 18 configurations (2 clean, 4 per flaw source), runs them through F1 (generic, 90 tasks),
F2 pooled (100 trap tasks) and F2 split (60 trap + 40 representative tasks), prices them with a shrunk
frequency x known-severity pipeline, prices them with 4 simulated underwriters (F3), and scores every forecaster
against realised loss in an n_e-conversation experience period measured by the same accounting.

Usage: python -m trustcurve.study3.sim_a <out.json> [reps] [procs]
"""

from __future__ import annotations

import itertools
import json
import sys
import time
import zlib
from multiprocessing import Pool

import numpy as np
from scipy import stats as sps

TYPES = ("cancel", "change", "cabin", "bags", "book", "certificate", "statement")
K = len(TYPES)
ST = TYPES.index("statement")
D = np.array([0.35, 0.30, 0.10, 0.15, 0.15, 0.15, 0.60])           # deployment opportunities per conversation
SEV_MED = np.array([500.0, 150, 300, 60, 200, 120, 300]); SEV_SIG, SEV_CAP = 0.8, 2000.0
BASE = 0.002
PI_D = np.array([0.32, 0.12, 0.02, 0.02, 0.04, 0.26, 0.22])          # designer's prior
PI_X = np.array([0.08, 0.12, 0.10, 0.20, 0.20, 0.05, 0.25])          # incident-like
UNI = np.full(K, 1 / K)
O_F1 = np.array([0.5, 0.3, 0.05, 0.01, 0.05, 0.01, 0.3])             # Study 2 pool profile
JUDGE_SENS, JUDGE_FP = 0.85, 0.005
SOURCES = ("clean",) * 2 + ("designed",) * 4 + ("external",) * 4 + ("mechanical",) * 4 + ("natural",) * 4
NC = len(SOURCES)
NONDES = np.array([s in ("external", "mechanical", "natural") for s in SOURCES])
DES = np.array([s == "designed" for s in SOURCES])
N_UW, UW_SIG, UW_BIAS, UW_NAT, UW_SEEN, N_TRANSCRIPTS = 4, 0.7, 0.4, 2.5, 1.5, 10
FLOOR = 0.05
B_DRAWS = 300
COST_UW, COST_EXP = 0.012, 0.045

_rng0 = np.random.default_rng(12345)
_sev = np.minimum(np.exp(np.log(SEV_MED)[None, :] + SEV_SIG * _rng0.standard_normal((400_000, K))), SEV_CAP)
E_SEV, SD_SEV = _sev.mean(0), _sev.std(0)
CLEAN_MEAN = float((BASE * D * E_SEV).sum())

GRID = {"lam": (0.8, 0.5, 0.2), "phi": (0.0, 0.05, 0.10), "e": (1, 3),
        "r": ((0.05, 0.4), (0.02, 0.15)), "n_e": (100, 200, 400)}


def draw_configs(rng, lam, r_rng):
    """True per-opportunity event probability p[c, k] (deployment conditions), flaw rate r[c, k] (0 if none)."""
    g = np.exp(0.5 * rng.standard_normal(NC))
    base = np.repeat((BASE * g)[:, None], K, 1)
    flaw = np.zeros((NC, K))
    for c, s in enumerate(SOURCES):
        if s == "clean":
            continue
        pi = {"designed": PI_D, "external": lam * PI_D + (1 - lam) * PI_X, "mechanical": UNI,
              "natural": lam * PI_D + (1 - lam) * UNI}[s]
        n_t = 1 if rng.random() < 0.6 else 2
        for k in rng.choice(K, size=n_t, replace=False, p=pi):
            flaw[c, k] = rng.uniform(*r_rng)
        if s == "natural":
            base[c] *= rng.uniform(1.5, 3)
    return base, flaw


def p_event(base, flaw):
    return 1 - (1 - base) * (1 - np.minimum(flaw, 1.0))


def measure(rng, present, fired):
    """Apply the statement judge (sensitivity, false positives) to fired events; other perils are exact."""
    m = fired.copy()
    st_f = fired[..., ST]
    m[..., ST] = (st_f & (rng.random(st_f.shape) < JUDGE_SENS)) | (present[..., ST] & ~st_f & (rng.random(st_f.shape) < JUDGE_FP))
    return m


def bench_f1(rng):
    return rng.random((90, K)) < O_F1[None, :], np.ones((90, K))                       # presence, enrichment


def trap_tasks(rng, n, phi, e):
    alloc = np.maximum(PI_D, phi); alloc = alloc / alloc.sum()
    prim = rng.choice(K, size=n, p=alloc)
    pres = rng.random((n, K)) < np.minimum(0.5 * D, 1)[None, :]
    pres[np.arange(n), prim] = rng.random(n) < 0.9
    enr = np.ones((n, K)); enr[np.arange(n), prim] = e
    return pres, enr


def bench_f2(rng, phi, e, split):
    if not split:
        pres, enr = trap_tasks(rng, 100, phi, e)
        return pres, enr, np.ones(100, bool)
    p1, e1 = trap_tasks(rng, 60, phi, e)
    p2 = rng.random((40, K)) < D[None, :]
    return np.vstack([p1, p2]), np.vstack([e1, np.ones((40, K))]), np.r_[np.zeros(60, bool), np.ones(40, bool)]


def run_bench(rng, base, flaw, pres, enr):
    """Measured events [c, t, k] for every configuration on the same tasks."""
    p = p_event(base[:, None, :], flaw[:, None, :] * enr[None, :, :])
    fired = pres[None] & (rng.random(p.shape) < p)
    return measure(rng, np.broadcast_to(pres[None], p.shape), fired)


def sign_flags(ev):
    """One-sided exact sign test over tasks, configuration vs clean reference (index 0), p < 0.05."""
    tot = ev.sum(2)
    plus, minus = (tot > tot[0:1]).sum(1), (tot < tot[0:1]).sum(1)
    n = plus + minus
    p = np.where(n > 0, sps.binom.sf(plus - 1, np.maximum(n, 1), 0.5), 1.0)
    return p < 0.05


def price(rng, ev, pres, use, n_e):
    """Shrunk per-type rate x deployment opportunity x known severity; 90% predictive interval at n_e."""
    x = ev[:, use, :].sum(1).astype(float)
    n = np.broadcast_to(pres[use].sum(0)[None, :], x.shape).astype(float)
    mu0 = np.clip(x.sum(0) / np.maximum(n.sum(0), 1), 1e-4, 0.5)
    a, b = 0.5 + x, 0.5 * (1 - mu0) / mu0 + n - x
    point = (a / (a + b) * D * E_SEV).sum(1)
    rates = rng.beta(np.repeat(a[None], B_DRAWS, 0), np.repeat(b[None], B_DRAWS, 0))           # B x C x K
    N = rng.poisson(n_e * D * rates)
    loss = np.maximum(N * E_SEV + np.sqrt(N) * SD_SEV * rng.standard_normal(N.shape), 0).sum(2) / n_e
    lo, hi = np.percentile(loss, [5, 95], axis=0)
    return point, lo, hi


def experience(rng, base, flaw, n_e):
    pres = rng.random((n_e, K)) < D[None, :]
    p = p_event(base, flaw)[:, None, :]
    fired = pres[None] & (rng.random((NC, n_e, K)) < p)
    m = measure(rng, np.broadcast_to(pres[None], fired.shape), fired)
    sev = np.minimum(np.exp(np.log(SEV_MED) + SEV_SIG * rng.standard_normal(m.shape)), SEV_CAP)
    return (m * sev).sum((1, 2)) / n_e


def underwriters(rng, ev_f1):
    v = np.where(np.array([s == "natural" for s in SOURCES]), UW_NAT, 1.0)
    idx = rng.choice(ev_f1.shape[1], N_TRANSCRIPTS, replace=False)
    seen = (ev_f1[:, idx, :].sum(2) > 0).sum(1)
    v = v * UW_SEEN ** seen
    prices = CLEAN_MEAN * v[None, :] * np.exp(UW_BIAS * rng.standard_normal()) * np.exp(UW_SIG * rng.standard_normal((N_UW, NC)))
    return np.median(prices, 0), prices.min(0) / 1.5, prices.max(0) * 1.5


def score(point, lo, hi, real):
    lf, lr = np.log(np.maximum(point, FLOOR)), np.log(np.maximum(real, FLOOR))
    return {"spearman": float(sps.spearmanr(point, real).statistic) if np.ptp(real) > 0 else 0.0,
            "medlog": float(np.median(np.abs(lf - lr))),
            "coverage": float(np.mean((real >= lo) & (real <= hi))),
            "medlog_flawed": float(np.median(np.abs(lf - lr)[2:])),
            "bias_flawed": float(np.median((lf - lr)[2:]))}


def one_rep(cell, rep):
    seed = zlib.crc32(json.dumps([cell, rep]).encode())
    rng = np.random.default_rng(seed)
    base, flaw = draw_configs(rng, cell["lam"], cell["r"])
    real = experience(rng, base, flaw, cell["n_e"])
    out = {}
    p1, e1 = bench_f1(rng)
    ev1 = run_bench(rng, base, flaw, p1, e1)
    out["F1"] = {"flags": sign_flags(ev1), "score": score(*price(rng, ev1, p1, np.ones(90, bool), cell["n_e"]), real)}
    for name, split in (("F2p", False), ("F2s", True)):
        p2, e2, use = bench_f2(rng, cell["phi"], cell["e"], split)
        ev2 = run_bench(rng, base, flaw, p2, e2)
        out[name] = {"flags": sign_flags(ev2), "score": score(*price(rng, ev2, p2, use, cell["n_e"]), real)}
    out["F3"] = {"score": score(*underwriters(rng, ev1), real)}
    single = [(int(np.flatnonzero(flaw[c])[0]) if (flaw[c] > 0).sum() == 1 else -1) for c in range(NC)]
    return out, single


def summarise(cell, reps):
    res = {f: {"det": {s: [] for s in ("designed", "external", "mechanical", "natural", "nondesigned")},
               "fp": [], "by_type": {t: [] for t in TYPES}} for f in ("F1", "F2p", "F2s")}
    sc = {f: [] for f in ("F1", "F2p", "F2s", "F3")}
    h = {"H2_F2p": [], "H2_F2s": [], "H1_F2p": [], "H3_F2p": [], "H3_F2s": [], "H4_F2p": [], "H4_F2s": [],
         "gap_F2p": [], "gap_F2s": []}
    src = np.array(SOURCES)
    for rep in range(reps):
        out, single = one_rep(cell, rep)
        for f in ("F1", "F2p", "F2s"):
            fl = out[f]["flags"]
            for s in ("designed", "external", "mechanical", "natural"):
                res[f]["det"][s].append(float(fl[src == s].mean()))
            res[f]["det"]["nondesigned"].append(float(fl[NONDES].mean()))
            res[f]["fp"].append(float(fl[1]))
            for c, k in enumerate(single):
                if k >= 0:
                    res[f]["by_type"][TYPES[k]].append(float(fl[c]))
        for f in sc:
            sc[f].append(out[f]["score"])
        for v in ("F2p", "F2s"):
            fl = out[v]["flags"]
            h[f"H2_{v}"].append(float(fl[NONDES].sum() >= 6))
            h[f"gap_{v}"].append(float(fl[DES].mean() - fl[NONDES].mean()))
            s1, s2, s3 = out["F1"]["score"], out[v]["score"], out["F3"]["score"]
            h[f"H3_{v}"].append(float(s2["medlog"] <= 0.5 * s1["medlog"] and s2["spearman"] >= s1["spearman"] + 0.3))
            h[f"H4_{v}"].append(float(s2["medlog"] < s3["medlog"]))
        h["H1_F2p"].append(float(out["F2p"]["flags"][DES].mean() >= 0.7))

    def ms(x):
        x = np.asarray(x, float)
        return [round(float(x.mean()), 4), round(float(x.std(ddof=1) / np.sqrt(len(x))), 4)] if len(x) > 1 else [None, None]

    summ = {"cell": {**cell, "r": list(cell["r"])}, "reps": reps,
            "cost_usd": round(NC * (90 + 100) * COST_UW + NC * cell["n_e"] * COST_EXP, 1)}
    for f in res:
        summ[f] = {"det": {s: ms(v) for s, v in res[f]["det"].items()}, "fp": ms(res[f]["fp"]),
                   "det_single_target_by_type": {t: ms(v) + [len(v)] for t, v in res[f]["by_type"].items()}}
    for f in sc:
        summ.setdefault(f, {})["score"] = {m: ms([s[m] for s in sc[f]]) for m in sc[f][0]}
    summ["P"] = {k: ms(v) for k, v in h.items()}
    return summ


def _work(args):
    return summarise(*args)


def main(out, reps=300, procs=8):
    cells = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    t0 = time.time()
    with Pool(procs) as pool:
        results = pool.map(_work, [(c, reps) for c in cells], chunksize=1)
    meta = {"reps": reps, "n_cells": len(cells), "seconds": round(time.time() - t0, 1), "E_SEV": E_SEV.round(1).tolist(),
            "CLEAN_MEAN": round(CLEAN_MEAN, 3), "grid": {k: [list(x) if isinstance(x, tuple) else x for x in v] for k, v in GRID.items()}}
    json.dump({"meta": meta, "cells": results}, open(out, "w"), indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 300, int(sys.argv[3]) if len(sys.argv) > 3 else 8)
