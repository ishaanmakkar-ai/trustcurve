"""Post-hoc robustness checks requested by review 5 (REVIEW.md). Not pre-registered; labelled as such.

Usage: PYTHONPATH=src python scripts/review5_checks.py > results/phase1/review5_checks.json
"""
import json
import math
import random
from collections import defaultdict
from statistics import mean

from trustcurve.phase1 import (by_task, cluster_ci, dbm, fail, load, mcnemar_majority, omission, sign_test, sign_test_diffs)

P = "results/phase1/"
cells = {"HxH": "results/pilot/breadth_runs.csv", "HxO": P + "e1_O_runs.csv", "HxS": P + "e1_S_runs.csv",
         "SxH": P + "p1b_breadth_runs.csv", "SxO": P + "e1x_SO_runs.csv", "SxS": P + "e1x_SS_runs.csv"}
C = {k: load(v) for k, v in cells.items()}
out = {"note": "post-hoc, review 5; not pre-registered"}

# 1. Exact task-level sign tests: E1 contrasts, E1x agent gaps and interactions, phase 1b
out["sign_tests"] = {}
for name, f in (("db_mismatch", dbm), ("failure", fail), ("omission", omission)):
    st = {"E1_O_minus_H": sign_test(C["HxH"], C["HxO"], f), "E1_S_minus_H": sign_test(C["HxH"], C["HxS"], f)}
    for c in "HOS":
        st[f"E1x_gap_{c}"] = sign_test(C[f"Hx{c}"], C[f"Sx{c}"], f)
    tm = {k: {t: mean(v) for t, v in by_task(rows, f).items()} for k, rows in C.items()}
    tasks = sorted(set.intersection(*(set(v) for v in tm.values())), key=int)
    for c in "OS":
        d = [(tm[f"Sx{c}"][t] - tm[f"Hx{c}"][t]) - (tm["SxH"][t] - tm["HxH"][t]) for t in tasks]
        st[f"E1x_interaction_{c}"] = sign_test_diffs(d)
    st["E1x_gap_O_per_task_nonzero"] = {t: tm["SxO"][t] - tm["HxO"][t] for t in tasks if tm["SxO"][t] != tm["HxO"][t]}
    out["sign_tests"][name] = st

out["e1_mcnemar_majority"] = {n: {a: mcnemar_majority(C["HxH"], C[f"Hx{a}"], f) for a in "OS"} for n, f in (("failure", fail), ("db_mismatch", dbm))}

# 2. Cluster-bootstrap 90% intervals for every cell rate (replacing run-level Wilson in tables)
out["cell_cluster_ci90"] = {k: {"db_mismatch": cluster_ci(v, dbm), "failure": cluster_ci(v, fail)} for k, v in C.items()}
E2 = load(P + "e2_runs.csv")
par = lambda r: str(r["task_id"]).split("-")[0]
out["e2_cluster_ci90"] = {"variants_failure_parent_cluster": cluster_ci(E2, fail, key=par),
                          "variants_dbm_parent_cluster": cluster_ci(E2, dbm, key=par)}

# 3. E2 observed-scale V_eff (includes run noise at r runs per variant), parent-bootstrap
def comps(tree):
    vm = {p: {v: mean(ys) for v, ys in vs.items()} for p, vs in tree.items()}
    s2_run = mean([sum((y - mean(ys)) ** 2 for y in ys) / (len(ys) - 1) for vs in tree.values() for ys in vs.values()])
    m = 2
    s2_vm = mean([sum((x - mean(v.values())) ** 2 for x in v.values()) / (len(v) - 1) for v in vm.values()])
    s2_var = max(s2_vm - s2_run / m, 0.0)
    pm = [mean(v.values()) for v in vm.values()]; k = mean(len(v) for v in vm.values())
    s2_par = max(sum((x - mean(pm)) ** 2 for x in pm) / (len(pm) - 1) - s2_vm / k, 0.0)
    return s2_par, s2_var, s2_run
tree = defaultdict(lambda: defaultdict(list))
for r in E2:
    tree[par(r)][r["task_id"]].append(dbm(r))
def veff(c, runs, V=5):
    sp, sv, sr = c; tot = sp + sv + sr / runs
    rho = sp / tot if tot else float("nan")
    return V / (1 + (V - 1) * rho)
pt = comps(tree); rng = random.Random(1); ps = list(tree); bs = {1: [], 2: []}
for _ in range(2000):
    samp = {str(i): tree[rng.choice(ps)] for i in range(len(ps))}
    c = comps(samp)
    for r in (1, 2):
        v = veff(c, r)
        if v == v:
            bs[r].append(v)
out["e2_veff_observed_scale"] = {f"{r}_run_per_variant": {"V_eff": round(veff(pt, r), 2),
                                 "ci90": [round(sorted(bs[r])[int(0.05 * len(bs[r]))], 2), round(sorted(bs[r])[int(0.95 * len(bs[r])) - 1], 2)],
                                 "p_ge_2": round(sum(v >= 2 for v in bs[r]) / len(bs[r]), 3), "p_ge_3": round(sum(v >= 3 for v in bs[r]) / len(bs[r]), 3)}
                                 for r in (1, 2)}
out["e2_components"] = [round(x, 4) for x in pt]

# 4. Pairing-artefact sensitivity: drop the artefact's $ omission on the two task-14 header-error runs
art = {("SxO", "14", "1")}
def om_fixed(k):
    return [0 if (k, r["task_id"], r["trial"]) in art else omission(r) for r in C[k]]
d_o = []
for t in sorted({r["task_id"] for r in C["SxO"]}, key=int):
    s_ = [o for o, r in zip(om_fixed("SxO"), C["SxO"]) if r["task_id"] == t]
    h_ = [omission(r) for r in C["HxO"] if r["task_id"] == t]
    d_o.append(mean(s_) - mean(h_))
out["omission_gap_O_without_artefact"] = round(mean(d_o), 4)
print(json.dumps(out, indent=1))
