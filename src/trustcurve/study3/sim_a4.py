"""Study 3 phase A' loop 4 (pre-registered in STUDY3.md §"A' loop 4", commit 9bbf26c): representativeness,
exposure-matched detection at the S0 per-task unit, a perfect-forecaster ceiling, 4 clean controls.

Forecasters: O (true expected loss), F1_1 (90 tasks x 1 run), F1_3 (90 x 3), F2 (60 trap + 40 representative x 3,
split pricing), F2p (pooled pricing, reported only). F1 tasks carry a flaw's trigger at rho1*q, F2 representative tasks
at rho2*q; anticipated trap tasks at 0.9, unanticipated at 0.5q (incidental trap opportunities at q, as loop 3).

Usage: python -m trustcurve.study3.sim_a4 <out.json> [reps] [procs]
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

from trustcurve.study3.sim_a import BASE, COST_EXP, COST_UW, D, K, O_F1, PI_D, PI_X, UNI, measure, sign_flags
from trustcurve.study3.sim_a2 import SEV, abslog, one_sided_sign, price

MED, ESEV, SDSEV = SEV["A"]
LAM, PHI, R_RUNS = 0.5, 0.10, 3
SRC = np.array(("clean",) * 4 + ("designed",) * 4 + ("external",) * 4 + ("mechanical",) * 4 + ("natural",) * 4)
NC = len(SRC)
DES, NOND, CLEAN = SRC == "designed", np.isin(SRC, ("external", "mechanical", "natural")), SRC == "clean"
FLAWED = ~CLEAN
GRID = {"rho1": (0.0, 0.3, 0.6, 1.0), "rho2": (0.3, 0.6, 1.0, 1.5), "r": ((0.05, 0.4), (0.02, 0.15)), "n_e": (100, 200, 400)}
R_BINS = (0.02, 0.05, 0.1, 0.2, 0.4)
JUDGE_USD, FIXED_USD, RETRY = 0.004, 25.0, 1.10


def draw(rng, r_rng):
    g = np.exp(0.5 * rng.standard_normal(NC))
    base = np.repeat((BASE * g)[:, None], K, 1)
    r = np.zeros((NC, K)); q = np.ones((NC, K)); ant = np.zeros((NC, K), bool)
    for c, s in enumerate(SRC):
        if s == "clean":
            continue
        pi = {"designed": PI_D, "external": LAM * PI_D + (1 - LAM) * PI_X, "mechanical": UNI,
              "natural": LAM * PI_D + (1 - LAM) * UNI}[s]
        for k in rng.choice(K, size=1 if rng.random() < 0.6 else 2, replace=False, p=pi):
            q[c, k] = rng.uniform(0.15, 0.6)
            r[c, k] = rng.uniform(r_rng[0], min(r_rng[1], q[c, k]))
            ant[c, k] = rng.random() < (0.8 if s == "designed" else 0.8 * LAM)
        if s == "natural":
            base[c] *= rng.uniform(1.5, 3)
    return base, r, q, ant


def runs(rng, base, r, q, pres, trig_p, R):
    """R runs on the same tasks (trigger is a task property). Returns events [c, R, t, k]."""
    trig = rng.random(trig_p.shape) < np.minimum(trig_p, 1)
    cond = np.where(r > 0, np.minimum(1, r / q), 0)[:, None, :]
    out = []
    for _ in range(R):
        ff = trig & (rng.random(trig_p.shape) < cond)
        fired = pres[None] & ((rng.random(trig_p.shape) < base[:, None, :]) | ff)
        out.append(measure(rng, np.broadcast_to(pres[None], fired.shape), fired))
    return np.stack(out, 1)


def experience(rng, base, r, q, n_e):
    pres = rng.random((n_e, K)) < D[None, :]
    ev = runs(rng, base, r, q, pres, np.broadcast_to(q[:, None, :], (NC, n_e, K)), 1)[:, 0]
    sev = np.minimum(np.exp(np.log(MED) + 0.8 * rng.standard_normal(ev.shape)), 2000.0)
    return (ev * sev).sum((1, 2)) / n_e


def oracle(rng, base, r, n_e):
    p = 1 - (1 - base) * (1 - r)
    point = (p * D * ESEV).sum(1)
    N = rng.poisson(n_e * D * np.broadcast_to(p, (300,) + p.shape))
    loss = np.maximum(N * ESEV + np.sqrt(N) * SDSEV * rng.standard_normal(N.shape), 0).sum(2) / n_e
    lo, hi = np.percentile(loss, [5, 95], axis=0)
    return point, lo, hi


def flags(ev, unit):
    """ev [c, R, t, k]; unit 'task' sums runs per task (S0); 'run' treats task-runs as units (sensitivity)."""
    if unit == "task":
        return sign_flags(ev.sum(1))
    c, R, t, k = ev.shape
    return sign_flags(ev.reshape(c, R * t, k))


def one_rep(cell, rep):
    rng = np.random.default_rng(zlib.crc32(json.dumps(["a4", cell, rep]).encode()))
    n_e = cell["n_e"]
    base, r, q, ant = draw(rng, cell["r"])
    real = experience(rng, base, r, q, n_e)
    out = {"O": oracle(rng, base, r, n_e)}
    p1 = rng.random((90, K)) < O_F1[None, :]
    ev1 = runs(rng, base, r, q, p1, np.broadcast_to(cell["rho1"] * q[:, None, :], (NC, 90, K)), R_RUNS)
    fl = {"F1_1": flags(ev1[:, :1], "task"), "F1_3": flags(ev1, "task"), "F1_3run": flags(ev1, "run")}
    out["F1_1"] = price(rng, ev1[:, 0], p1, np.ones(90, bool), n_e, ESEV, SDSEV)
    out["F1_3"] = price(rng, ev1.reshape(NC, -1, K), np.tile(p1, (R_RUNS, 1)), np.ones(90 * R_RUNS, bool), n_e, ESEV, SDSEV)
    # F2: 60 trap tasks (allocation max(pi_D, phi)) + 40 representative tasks
    alloc = np.maximum(PI_D, PHI); alloc = alloc / alloc.sum()
    prim = rng.choice(K, size=60, p=alloc)
    pt = rng.random((60, K)) < np.minimum(0.5 * D, 1)[None, :]
    pt[np.arange(60), prim] = rng.random(60) < 0.9
    pr = rng.random((40, K)) < D[None, :]
    pres = np.vstack([pt, pr])
    tp = np.empty((NC, 100, K))
    is_prim = np.zeros((60, K), bool); is_prim[np.arange(60), prim] = True
    tp[:, :60] = np.where(is_prim[None], np.where(ant[:, None, :], 0.9, 0.5 * q[:, None, :]), q[:, None, :])
    tp[:, 60:] = cell["rho2"] * q[:, None, :]
    ev2 = runs(rng, base, r, q, pres, tp, R_RUNS)
    fl["F2"], fl["F2run"] = flags(ev2, "task"), flags(ev2, "run")
    presR = np.tile(pres, (R_RUNS, 1)); flat2 = ev2.reshape(NC, -1, K)
    use = np.tile(np.r_[np.zeros(60, bool), np.ones(40, bool)], R_RUNS)
    out["F2"] = price(rng, flat2, presR, use, n_e, ESEV, SDSEV)
    out["F2p"] = price(rng, flat2, presR, np.ones(len(use), bool), n_e, ESEV, SDSEV)
    rmax = r.max(1)
    return out, fl, real, rmax


def spear(a, b):
    return float(sps.spearmanr(a, b).statistic) if np.ptp(b) > 0 and np.ptp(a) > 0 else 0.0


def summarise(cell, reps):
    P = ("O", "F1_1", "F1_3", "F2", "F2p")
    pr = {f: {m: [] for m in ("medlog", "spearman", "cov", "bias_flawed")} for f in P}
    det = {f: {m: [] for m in ("des", "nondes", "fp")} for f in ("F1_1", "F1_3", "F2", "F1_3run", "F2run")}
    t = {m: [] for m in ("mcnemar_matched", "mcnemar_unmatched", "mcnemar_matched_run", "did", "did_run",
                         "H3b", "H3b_ceiling", "H3_F2", "H3_O", "H3_F2_vsF1_1", "H2_F2", "H2_F1_3")}
    curve = {f: [[0, 0] for _ in range(len(R_BINS) - 1)] for f in ("F1_3", "F2")}
    for rep in range(reps):
        out, fl, real, rmax = one_rep(cell, rep)
        err = {f: abslog(out[f][0], real) for f in P}
        for f in P:
            pt, lo, hi = out[f]
            pr[f]["medlog"].append(float(np.median(err[f]))); pr[f]["spearman"].append(spear(pt, real))
            pr[f]["cov"].append(float(np.mean((real >= lo) & (real <= hi))))
            pr[f]["bias_flawed"].append(float(np.median((np.log(np.maximum(pt, 0.05)) - np.log(np.maximum(real, 0.05)))[FLAWED])))
        for f in det:
            det[f]["des"].append(fl[f][DES].mean()); det[f]["nondes"].append(fl[f][NOND].mean())
            det[f]["fp"].append(fl[f][1:4].mean())
        mc = lambda a, b: float(one_sided_sign(int((a & ~b)[FLAWED].sum()), int((b & ~a)[FLAWED].sum())))
        t["mcnemar_matched"].append(mc(fl["F2"], fl["F1_3"])); t["mcnemar_unmatched"].append(mc(fl["F2"], fl["F1_1"]))
        t["mcnemar_matched_run"].append(mc(fl["F2run"], fl["F1_3run"]))
        gap = lambda f: fl[f][DES].mean() - fl[f][NOND].mean()
        t["did"].append(gap("F2") - gap("F1_3")); t["did_run"].append(gap("F2run") - gap("F1_3run"))
        sg = lambda a, b: float(one_sided_sign(int((err[a] < err[b]).sum()), int((err[a] > err[b]).sum())))
        t["H3b"].append(sg("F2", "F1_3")); t["H3b_ceiling"].append(sg("O", "F1_3"))
        h3 = lambda a, b: float(np.median(err[a]) <= 0.5 * np.median(err[b]) and
                                spear(out[a][0], real) >= spear(out[b][0], real) + 0.3)
        t["H3_F2"].append(h3("F2", "F1_3")); t["H3_O"].append(h3("O", "F1_3")); t["H3_F2_vsF1_1"].append(h3("F2", "F1_1"))
        t["H2_F2"].append(float(fl["F2"][NOND].mean() >= 0.5)); t["H2_F1_3"].append(float(fl["F1_3"][NOND].mean() >= 0.5))
        for f in curve:
            for c in np.flatnonzero(FLAWED):
                b = int(np.clip(np.searchsorted(R_BINS, rmax[c], side="right") - 1, 0, len(R_BINS) - 2))
                curve[f][b][0] += int(fl[f][c]); curve[f][b][1] += 1

    def ms(x):
        x = np.asarray(x, float)
        return [round(float(x.mean()), 4), round(float(x.std(ddof=1) / np.sqrt(len(x))), 4)]

    n_e = cell["n_e"]
    uw = NC * (90 + 100) * R_RUNS * COST_UW
    ex = NC * n_e * COST_EXP
    judge = JUDGE_USD * NC * ((90 + 100) * R_RUNS + n_e)
    summ = {"cell": {**cell, "r": list(cell["r"])}, "reps": reps,
            "cost": {"underwriting": round(uw, 1), "experience": round(ex, 1), "judge_est": round(judge, 1),
                     "fixed": FIXED_USD, "total_with_retries": round((uw + ex + judge + FIXED_USD) * RETRY, 1)},
            "pricing": {f: {m: ms(v) for m, v in d.items()} for f, d in pr.items()},
            "detection": {f: {m: ms(v) for m, v in d.items()} for f, d in det.items()},
            "tests": {m: ms(v) for m, v in t.items()},
            "did_sd": round(float(np.std(t["did"], ddof=1)), 4),
            "did_w90": round(float(np.percentile(t["did"], 95) - np.percentile(t["did"], 5)), 4),
            "curve": {f: [{"bin": [R_BINS[i], R_BINS[i + 1]], "flagged": a, "n": n,
                           "rate": round(a / n, 4) if n else None} for i, (a, n) in enumerate(v)] for f, v in curve.items()}}
    return summ


def _work(a):
    return summarise(*a)


def main(out, reps=300, procs=8):
    cells = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    t0 = time.time()
    with Pool(procs) as pool:
        res = pool.map(_work, [(c, reps) for c in cells], chunksize=1)
    meta = {"reps": reps, "n_cells": len(cells), "seconds": round(time.time() - t0, 1), "prereg_commit": "9bbf26c",
            "grid": {k: [list(x) if isinstance(x, tuple) else x for x in v] for k, v in GRID.items()}}
    json.dump({"meta": meta, "cells": res}, open(out, "w"), indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 300, int(sys.argv[3]) if len(sys.argv) > 3 else 8)
