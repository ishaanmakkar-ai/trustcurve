"""Phase A loop-1 diagnostic: does per-configuration severity heterogeneity explain parameter under-coverage?"""
import sys
from multiprocessing import Pool

import numpy as np

import trustcurve.study2.sim_a as A


def run(args):
    sevc, seed = args
    A.SIGMA_SEVC = sevc
    return A.one_rep("S0", 180, 200, seed)


if __name__ == "__main__":
    out = []
    for sevc in (0.2, 0.0):
        with Pool(7) as p:
            reps = p.map(run, [(sevc, 900000 + i) for i in range(140)])
        for m in ("M1", "M2"):
            cp = np.mean([x for r in reps for x in r[m]["cov_param"]]); cr = np.mean([x for r in reps for x in r[m]["cov_pred"]])
            line = f"SIGMA_SEVC={sevc} {m}: cov_param {cp:.3f} cov_pred {cr:.3f}"
            print(line, flush=True); out.append(line)
    open(sys.argv[1], "w").write("\n".join(out) + "\n")
