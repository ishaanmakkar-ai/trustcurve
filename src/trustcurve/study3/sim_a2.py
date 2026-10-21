"""Study 3 phase A' loop 2 (pre-registered in STUDY3.md §"A' loop 2"): when can test design matter?

Adds to loop 1 (sim_a.py, reused): a severity profile S (A = loop 1, B = flat $300 medians), R runs per F2 task,
H2 discrimination against F1, paired detection power (exact McNemar F2 vs F1 over the 16 flawed configurations),
paired pricing power (sign test on per-configuration |log error|) and the blind-spot loss share.

Usage: python -m trustcurve.study3.sim_a2 <out.json> [reps] [procs]
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

from trustcurve.study3 import sim_a as A
from trustcurve.study3.sim_a import (D, DES, FLOOR, K, NC, NONDES, SEV_CAP, SEV_SIG, SOURCES, TYPES, bench_f1,
                                     bench_f2, draw_configs, measure, p_event, run_bench, sign_flags)

PROFILES = {"A": A.SEV_MED, "B": np.full(K, 300.0)}
_r0 = np.random.default_rng(54321)
_Z = _r0.standard_normal((400_000, K))
SEV = {}
for s, med in PROFILES.items():
    x = np.minimum(np.exp(np.log(med)[None, :] + SEV_SIG * _Z), SEV_CAP)
    SEV[s] = (med, x.mean(0), x.std(0))

GRID = {"lam": (0.5, 0.2), "phi": (0.0, 0.10), "e": (1, 3), "r": ((0.05, 0.4), (0.02, 0.15)),
        "n_e": (100, 200, 400), "S": ("A", "B"), "R": (1, 3)}
BLIND = ("cabin", "bags", "book", "certificate")


def tile(pres, enr, use, R):
    return np.tile(pres, (R, 1)), np.tile(enr, (R, 1)), np.tile(use, R)


def price(rng, ev, pres, use, n_e, esev, sdsev):
    x = ev[:, use, :].sum(1).astype(float)
    n = np.broadcast_to(pres[use].sum(0)[None, :], x.shape).astype(float)
    mu0 = np.clip(x.sum(0) / np.maximum(n.sum(0), 1), 1e-4, 0.5)
    a, b = 0.5 + x, 0.5 * (1 - mu0) / mu0 + n - x
    point = (a / (a + b) * D * esev).sum(1)
    rates = rng.beta(np.repeat(a[None], A.B_DRAWS, 0), np.repeat(b[None], A.B_DRAWS, 0))
    N = rng.poisson(n_e * D * rates)
    loss = np.maximum(N * esev + np.sqrt(N) * sdsev * rng.standard_normal(N.shape), 0).sum(2) / n_e
    lo, hi = np.percentile(loss, [5, 95], axis=0)
    return point, lo, hi


def experience(rng, base, flaw, n_e, med):
    pres = rng.random((n_e, K)) < D[None, :]
    fired = pres[None] & (rng.random((NC, n_e, K)) < p_event(base, flaw)[:, None, :])
    m = measure(rng, np.broadcast_to(pres[None], fired.shape), fired)
    sev = np.minimum(np.exp(np.log(med) + SEV_SIG * rng.standard_normal(m.shape)), SEV_CAP)
    return (m * sev).sum((1, 2)) / n_e


def abslog(point, real):
    return np.abs(np.log(np.maximum(point, FLOOR)) - np.log(np.maximum(real, FLOOR)))


def one_sided_sign(plus, minus):
    n = plus + minus
    return bool(n > 0 and sps.binom.sf(plus - 1, n, 0.5) < 0.05)


def one_rep(cell, rep):
    rng = np.random.default_rng(zlib.crc32(json.dumps(["a2", cell, rep]).encode()))
    med, esev, sdsev = SEV[cell["S"]]
    base, flaw = draw_configs(rng, cell["lam"], cell["r"])
    real = experience(rng, base, flaw, cell["n_e"], med)
    p1, e1 = bench_f1(rng)
    ev1 = run_bench(rng, base, flaw, p1, e1)
    f1_flags = sign_flags(ev1)
    pt1 = price(rng, ev1, p1, np.ones(90, bool), cell["n_e"], esev, sdsev)
    out = {"F1": {"flags": f1_flags, "point": pt1[0], "lo": pt1[1], "hi": pt1[2]}}
    for name, split in (("F2p", False), ("F2s", True)):
        p2, e2, use = tile(*bench_f2(rng, cell["phi"], cell["e"], split), cell["R"])
        ev2 = run_bench(rng, base, flaw, p2, e2)
        pt = price(rng, ev2, p2, use, cell["n_e"], esev, sdsev)
        out[name] = {"flags": sign_flags(ev2), "point": pt[0], "lo": pt[1], "hi": pt[2]}
    n1 = p1.sum(0)
    blind = np.array([n1[k] < 5 for k in range(K)])
    flaw_loss = (p_event(base, flaw) - base) * D * esev
    share = float(flaw_loss[:, blind].sum() / max(flaw_loss.sum(), 1e-12))
    single = [(int(np.flatnonzero(flaw[c])[0]) if (flaw[c] > 0).sum() == 1 else -1) for c in range(NC)]
    return out, real, share, single


def summarise(cell, reps):
    keys = ("F2p", "F2s")
    acc = {k: [] for k in ("share",)}
    per = {v: {m: [] for m in ("det_des", "det_nondes", "H2", "mcnemar", "medlog", "spearman", "cov", "bias_flawed",
                                "H3", "f2_better_medlog", "pricing_sign", "sp_plus01")} for v in keys}
    f1 = {m: [] for m in ("det_des", "det_nondes", "H2", "medlog", "spearman", "cov")}
    by_type = {v: {t: [] for t in TYPES} for v in ("F1",) + keys}
    flawed = np.array([s != "clean" for s in SOURCES])
    for rep in range(reps):
        out, real, share, single = one_rep(cell, rep)
        acc["share"].append(share)
        e1 = abslog(out["F1"]["point"], real)
        sp1 = float(sps.spearmanr(out["F1"]["point"], real).statistic) if np.ptp(real) > 0 else 0.0
        fl1 = out["F1"]["flags"]
        f1["det_des"].append(fl1[DES].mean()); f1["det_nondes"].append(fl1[NONDES].mean())
        f1["H2"].append(float(fl1[NONDES].sum() >= 6)); f1["medlog"].append(float(np.median(e1))); f1["spearman"].append(sp1)
        f1["cov"].append(float(np.mean((real >= out["F1"]["lo"]) & (real <= out["F1"]["hi"]))))
        for c, k in enumerate(single):
            if k >= 0:
                for v in ("F1",) + keys:
                    by_type[v][TYPES[k]].append(float(out[v]["flags"][c]))
        for v in keys:
            o = out[v]; fl = o["flags"]; e2 = abslog(o["point"], real)
            sp2 = float(sps.spearmanr(o["point"], real).statistic) if np.ptp(real) > 0 else 0.0
            P = per[v]
            P["det_des"].append(fl[DES].mean()); P["det_nondes"].append(fl[NONDES].mean())
            P["H2"].append(float(fl[NONDES].sum() >= 6))
            b, c = int((fl & ~fl1)[flawed].sum()), int((fl1 & ~fl)[flawed].sum())
            P["mcnemar"].append(float(one_sided_sign(b, c)))
            P["medlog"].append(float(np.median(e2))); P["spearman"].append(sp2)
            P["cov"].append(float(np.mean((real >= o["lo"]) & (real <= o["hi"]))))
            P["bias_flawed"].append(float(np.median((np.log(np.maximum(o["point"], FLOOR)) - np.log(np.maximum(real, FLOOR)))[flawed])))
            P["H3"].append(float(np.median(e2) <= 0.5 * np.median(e1) and sp2 >= sp1 + 0.3))
            P["f2_better_medlog"].append(float(np.median(e2) < np.median(e1)))
            P["pricing_sign"].append(float(one_sided_sign(int((e2 < e1).sum()), int((e2 > e1).sum()))))
            P["sp_plus01"].append(float(sp2 - sp1 >= 0.1))

    def ms(x):
        x = np.asarray(x, float)
        return [round(float(x.mean()), 4), round(float(x.std(ddof=1) / np.sqrt(len(x))), 4), len(x)] if len(x) > 1 else [None, None, len(x)]

    sh = np.asarray(acc["share"])
    hi = sh >= 0.5
    summ = {"cell": {**cell, "r": list(cell["r"])}, "reps": reps,
            "cost_usd": round(NC * (90 + 100 * cell["R"]) * A.COST_UW + NC * cell["n_e"] * A.COST_EXP, 1),
            "blind_share": ms(sh), "share_ge_05": round(float(hi.mean()), 4),
            "F1": {m: ms(v) for m, v in f1.items()},
            "by_type": {v: {t: ms(x) for t, x in d.items()} for v, d in by_type.items()}}
    for v in keys:
        summ[v] = {m: ms(x) for m, x in per[v].items()}
        summ[v]["H2_discrimination"] = round(float(np.mean(per[v]["H2"]) - np.mean(f1["H2"])), 4)
        summ[v]["given_share_ge_05"] = {m: ms(np.asarray(per[v][m])[hi]) for m in ("H3", "pricing_sign", "f2_better_medlog")}
    return summ


def _work(args):
    return summarise(*args)


def main(out, reps=300, procs=8):
    cells = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    t0 = time.time()
    with Pool(procs) as pool:
        res = pool.map(_work, [(c, reps) for c in cells], chunksize=1)
    meta = {"reps": reps, "n_cells": len(cells), "seconds": round(time.time() - t0, 1),
            "E_SEV": {s: v[1].round(1).tolist() for s, v in SEV.items()},
            "grid": {k: [list(x) if isinstance(x, tuple) else x for x in v] for k, v in GRID.items()}}
    json.dump({"meta": meta, "cells": res}, open(out, "w"), indent=1)
    print(json.dumps(meta))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 300, int(sys.argv[3]) if len(sys.argv) > 3 else 8)
