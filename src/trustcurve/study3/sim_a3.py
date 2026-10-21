"""Study 3 phase A' loop 3 (pre-registered in STUDY3.md §"A' loop 3"): within-type triggers and anticipation.

Each flaw fires only on opportunities of its type that carry its trigger condition (deployment prevalence q). Generic
(F1) and representative F2 tasks carry the trigger at q; F2 trap tasks on the flaw's type carry it with probability
0.9 if the designer anticipated it, else 0.5 q. P(anticipated) = 0.8 for designed flaws, 0.8 lambda otherwise.
Severity profile S_A; flaw rate r ~ U(0.05, 0.4) per opportunity in deployment; F2 pricing uses the adopted split.

Usage: python -m trustcurve.study3.sim_a3 <out.json> [reps] [procs]
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

from trustcurve.study3.sim_a import BASE, COST_EXP, COST_UW, D, FLOOR, K, O_F1, PI_D, PI_X, UNI, measure, sign_flags
from trustcurve.study3.sim_a2 import SEV, abslog, one_sided_sign, price

MED, ESEV, SDSEV = SEV["A"]
R_RNG = (0.05, 0.4)
SIZES = {18: (4, 200), 30: (7, 120)}          # configurations -> (configurations per source, n_e)
GRID = {"lam": (0.8, 0.5, 0.2), "phi": (0.0, 0.10), "R": (1, 3), "size": (18, 30)}


def sources(per):
    return ("clean",) * 2 + ("designed",) * per + ("external",) * per + ("mechanical",) * per + ("natural",) * per


def draw(rng, src, lam):
    nc = len(src)
    g = np.exp(0.5 * rng.standard_normal(nc))
    base = np.repeat((BASE * g)[:, None], K, 1)
    r = np.zeros((nc, K)); q = np.ones((nc, K)); ant = np.zeros((nc, K), bool)
    for c, s in enumerate(src):
        if s == "clean":
            continue
        pi = {"designed": PI_D, "external": lam * PI_D + (1 - lam) * PI_X, "mechanical": UNI,
              "natural": lam * PI_D + (1 - lam) * UNI}[s]
        for k in rng.choice(K, size=1 if rng.random() < 0.6 else 2, replace=False, p=pi):
            r[c, k] = rng.uniform(*R_RNG); q[c, k] = rng.uniform(0.15, 0.6)
            ant[c, k] = rng.random() < (0.8 if s == "designed" else 0.8 * lam)
        if s == "natural":
            base[c] *= rng.uniform(1.5, 3)
    return base, r, q, ant


def run(rng, base, r, q, pres, trig_p):
    """pres [t, k]; trig_p [c, t, k] trigger probability; returns measured events [c, t, k]."""
    trig = rng.random(trig_p.shape) < trig_p
    fire_flaw = trig & (rng.random(trig_p.shape) < np.minimum(1, r / q)[:, None, :])
    fired = pres[None] & ((rng.random(trig_p.shape) < base[:, None, :]) | (fire_flaw & (r[:, None, :] > 0)))
    return measure(rng, np.broadcast_to(pres[None], fired.shape), fired)


def run_tasks(rng, base, r, q, pres, trig_p, R):
    """R runs on the same tasks: trigger presence is a task property, firing is redrawn each run."""
    trig = rng.random(trig_p.shape) < trig_p
    out = []
    for _ in range(R):
        fire_flaw = trig & (rng.random(trig_p.shape) < np.minimum(1, r / q)[:, None, :])
        fired = pres[None] & ((rng.random(trig_p.shape) < base[:, None, :]) | (fire_flaw & (r[:, None, :] > 0)))
        out.append(measure(rng, np.broadcast_to(pres[None], fired.shape), fired))
    return np.concatenate(out, 1), np.tile(pres, (R, 1))


def f2_tasks(rng, phi, q, ant, n_trap, n_rep):
    alloc = np.maximum(PI_D, phi); alloc = alloc / alloc.sum()
    prim = rng.choice(K, size=n_trap, p=alloc)
    pt = rng.random((n_trap, K)) < np.minimum(0.5 * D, 1)[None, :]
    pt[np.arange(n_trap), prim] = rng.random(n_trap) < 0.9
    pr = rng.random((n_rep, K)) < D[None, :]
    pres = np.vstack([pt, pr])
    nc = q.shape[0]
    tp = np.repeat(q[:, None, :], n_trap + n_rep, 1).copy()
    is_prim = np.zeros((n_trap, K), bool); is_prim[np.arange(n_trap), prim] = True
    trap_p = np.where(ant[:, None, :], 0.9, 0.5 * q[:, None, :])
    tp[:, :n_trap, :] = np.where(is_prim[None], trap_p, q[:, None, :])
    use = np.r_[np.zeros(n_trap, bool), np.ones(n_rep, bool)]
    return pres, tp, use


def experience(rng, base, r, q, n_e):
    pres = rng.random((n_e, K)) < D[None, :]
    nc = base.shape[0]
    ev = run(rng, base, r, q, pres, np.broadcast_to(q[:, None, :], (nc, n_e, K)))
    sev = np.minimum(np.exp(np.log(MED) + 0.8 * rng.standard_normal(ev.shape)), 2000.0)
    return (ev * sev).sum((1, 2)) / n_e


def one_rep(cell, rep):
    rng = np.random.default_rng(zlib.crc32(json.dumps(["a3", cell, rep]).encode()))
    per, n_e = SIZES[cell["size"]]
    src = np.array(sources(per)); nc = len(src)
    base, r, q, ant = draw(rng, src, cell["lam"])
    real = experience(rng, base, r, q, n_e)
    p1 = rng.random((90, K)) < O_F1[None, :]
    ev1, _ = run_tasks(rng, base, r, q, p1, np.broadcast_to(q[:, None, :], (nc, 90, K)), 1)
    fl1 = sign_flags(ev1)
    pt1 = price(rng, ev1, p1, np.ones(90, bool), n_e, ESEV, SDSEV)
    out = {"F1": (fl1, pt1)}
    for name, (nt, nr) in (("F2s", (60, 40)), ("F2p", (100, 0))):
        pres, tp, use = f2_tasks(rng, cell["phi"], q, ant, nt, nr)
        ev2, presR = run_tasks(rng, base, r, q, pres, tp, cell["R"])
        useR = np.tile(use if use.any() else np.ones(len(use), bool), cell["R"])
        out[name] = (sign_flags(ev2), price(rng, ev2, presR, useR, n_e, ESEV, SDSEV))
    flawed = (r > 0).any(1)
    anticipated = (ant & (r > 0)).any(1)
    return src, out, real, flawed, anticipated


def summarise(cell, reps):
    keys = ("det_des", "det_nondes", "det_nondes_anticipated", "det_nondes_unanticipated", "H1", "H2", "gap", "H5",
            "mcnemar", "medlog", "spearman", "f2_better_medlog", "H3b_sign", "H3", "sp_plus01")
    acc = {v: {k: [] for k in keys} for v in ("F2s", "F2p")}
    f1 = {k: [] for k in ("det_des", "det_nondes", "H2", "medlog", "spearman")}
    for rep in range(reps):
        src, out, real, flawed, antic = one_rep(cell, rep)
        des, nond = src == "designed", np.isin(src, ("external", "mechanical", "natural"))
        fl1, pt1 = out["F1"]; e1 = abslog(pt1[0], real)
        sp1 = float(sps.spearmanr(pt1[0], real).statistic) if np.ptp(real) > 0 else 0.0
        f1["det_des"].append(fl1[des].mean()); f1["det_nondes"].append(fl1[nond].mean())
        f1["H2"].append(float(fl1[nond].mean() >= 0.5)); f1["medlog"].append(float(np.median(e1))); f1["spearman"].append(sp1)
        for v in ("F2s", "F2p"):
            fl, pt = out[v]; e2 = abslog(pt[0], real)
            sp2 = float(sps.spearmanr(pt[0], real).statistic) if np.ptp(real) > 0 else 0.0
            A = acc[v]
            A["det_des"].append(fl[des].mean()); A["det_nondes"].append(fl[nond].mean())
            if (nond & antic).any():
                A["det_nondes_anticipated"].append(fl[nond & antic].mean())
            if (nond & ~antic).any():
                A["det_nondes_unanticipated"].append(fl[nond & ~antic].mean())
            A["H1"].append(float(fl[des].mean() >= 0.7)); A["H2"].append(float(fl[nond].mean() >= 0.5))
            gap = fl[des].mean() - fl[nond].mean(); A["gap"].append(gap); A["H5"].append(float(gap <= 0.25))
            A["mcnemar"].append(float(one_sided_sign(int((fl & ~fl1)[flawed].sum()), int((fl1 & ~fl)[flawed].sum()))))
            A["medlog"].append(float(np.median(e2))); A["spearman"].append(sp2)
            A["f2_better_medlog"].append(float(np.median(e2) < np.median(e1)))
            A["H3b_sign"].append(float(one_sided_sign(int((e2 < e1).sum()), int((e2 > e1).sum()))))
            A["H3"].append(float(np.median(e2) <= 0.5 * np.median(e1) and sp2 >= sp1 + 0.3))
            A["sp_plus01"].append(float(sp2 - sp1 >= 0.1))

    def ms(x):
        x = np.asarray(x, float)
        return [round(float(x.mean()), 4), round(float(x.std(ddof=1) / np.sqrt(len(x))), 4), len(x)] if len(x) > 1 else [None, None, len(x)]

    nc = cell["size"]
    summ = {"cell": cell, "reps": reps,
            "cost_usd": round(nc * (90 + 100 * cell["R"]) * COST_UW + 3600 * COST_EXP, 1),
            "F1": {k: ms(v) for k, v in f1.items()}}
    for v in acc:
        summ[v] = {k: ms(x) for k, x in acc[v].items()}
        summ[v]["H2_discrimination"] = round(float(np.mean(acc[v]["H2"]) - np.mean(f1["H2"])), 4)
    return summ


def _work(a):
    return summarise(*a)


def main(out, reps=400, procs=8):
    cells = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    t0 = time.time()
    with Pool(procs) as pool:
        res = pool.map(_work, [(c, reps) for c in cells], chunksize=1)
    meta = {"reps": reps, "n_cells": len(cells), "seconds": round(time.time() - t0, 1), "grid": GRID, "sizes": SIZES}
    json.dump({"meta": meta, "cells": res}, open(out, "w"), indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 400, int(sys.argv[3]) if len(sys.argv) > 3 else 8)
