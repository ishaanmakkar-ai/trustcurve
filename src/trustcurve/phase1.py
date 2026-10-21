"""Phase 1 analyses (E1, E2, E3, reference run, phase 1b), as pre-registered in EXPERIMENTS.md."""

from __future__ import annotations

import csv
import json
import math
import random
import sys
from collections import defaultdict
from statistics import mean

from trustcurve.stats import icc_binary, wilson, zero_event_upper

Z90, Z80 = 1.6449, 0.8416


def load(path):
    return list(csv.DictReader(open(path)))


def attach_labels(rows, labels_path):
    if not labels_path:
        return rows
    lab = {(l["task_id"], l["trial"]): l for l in load(labels_path)}
    for r in rows:
        r.update({f"lab_{k}": v for k, v in lab.get((r["task_id"], r["trial"]), {}).items() if k not in ("task_id", "trial")})
    return rows


def fail(r):
    return int(r["reward"] != "1.0")


def dbm(r):
    return int(r["db_match"] != "True")


def insured(r):
    return int(r.get("insured_loss_event") == "True")


def by_task(rows, f):
    d = defaultdict(list)
    for r in rows:
        d[str(r["task_id"]).split("-")[0] if False else str(r["task_id"])].append(f(r))
    return d


def rate_summary(rows):
    n = len(rows); T = len({r["task_id"] for r in rows})
    out = {"runs": n, "tasks": T}
    for name, f in (("failure", fail), ("db_mismatch", dbm), ("insured_loss", insured)):
        x = sum(f(r) for r in rows)
        out[name] = {"count": x, "rate": round(x / n, 4), "wilson90": [round(v, 4) for v in wilson(x, n, Z90)]}
    out["insured_loss"]["robust_upper95_tasks"] = round(zero_event_upper(T), 4) if out["insured_loss"]["count"] == 0 else None
    out["omission_runs"] = sum(float(r.get("omission_usd") or 0) > 0 for r in rows)
    att = defaultdict(int)
    for r in rows:
        if fail(r) or dbm(r):
            att[r.get("lab_attribution") or "unlabelled"] += 1
    out["attribution"] = dict(att)
    out["icc_failure"] = round(icc_binary(by_task(rows, fail)), 3)
    out["icc_db_mismatch"] = round(icc_binary(by_task(rows, dbm)), 3)
    out["cost_usd"] = round(sum(float(r["cost_usd_from_tokens"] or 0) for r in rows), 4)
    return out


def paired(a_rows, b_rows, f, B=5000, seed=1):
    """Per-task paired difference (b - a) in mean outcome; task bootstrap 90% CI; MDE at 80% power."""
    A, Bt = by_task(a_rows, f), by_task(b_rows, f)
    tasks = sorted(set(A) & set(Bt))
    d = [mean(Bt[t]) - mean(A[t]) for t in tasks]
    rng = random.Random(seed); boots = []
    for _ in range(B):
        s = [d[rng.randrange(len(d))] for _ in d]; boots.append(mean(s))
    boots.sort()
    sd = (sum((x - mean(d)) ** 2 for x in d) / max(len(d) - 1, 1)) ** 0.5
    flips = sum(1 for t in tasks if (mean(A[t]) >= 0.5) != (mean(Bt[t]) >= 0.5))
    return {"tasks": len(tasks), "mean_diff": round(mean(d), 4), "ci90": [round(boots[int(0.05 * B)], 4), round(boots[int(0.95 * B) - 1], 4)],
            "mde80_two_sided_alpha10": round((Z90 + Z80) * sd / math.sqrt(len(d)), 4), "majority_flips": flips}


def e1(h_csv, o_csv, s_csv, labels=(None, None, None)):
    H, O, S = (attach_labels(load(p), l) for p, l in zip((h_csv, o_csv, s_csv), labels))
    res = {"arms": {"H_haiku_sim": rate_summary(H), "O_openai_sim": rate_summary(O), "S_sonnet_sim": rate_summary(S)}}
    for name, f in (("failure", fail), ("db_mismatch", dbm)):
        res[f"paired_{name}"] = {"O_minus_H": paired(H, O, f), "S_minus_H": paired(H, S, f), "S_minus_O": paired(O, S, f)}
    return res


def nested_components(rows, f=dbm, seed=1, B=2000):
    """3-level (parent / variant / run) method-of-moments variance components, balanced-ish design."""
    tree = defaultdict(lambda: defaultdict(list))
    for r in rows:
        tid = str(r["task_id"]); parent = tid.split("-")[0]
        tree[parent][tid].append(f(r))

    def comps(tr):
        # variant means; within-variant (run) variance; between-variant within-parent; between-parent
        vm = {p: {v: mean(ys) for v, ys in vs.items()} for p, vs in tr.items()}
        runs = [len(ys) for vs in tr.values() for ys in vs.values()]
        m = mean(runs)
        s2_run = mean([sum((y - mean(ys)) ** 2 for y in ys) / (len(ys) - 1) for vs in tr.values() for ys in vs.values() if len(ys) > 1])
        within_p = [sum((x - mean(list(v.values()))) ** 2 for x in v.values()) / (len(v) - 1) for v in vm.values() if len(v) > 1]
        s2_vm_within = mean(within_p)
        s2_var = max(s2_vm_within - s2_run / m, 0.0)
        pm = [mean(list(v.values())) for v in vm.values()]
        k = mean([len(v) for v in vm.values()])
        s2_pm = sum((x - mean(pm)) ** 2 for x in pm) / (len(pm) - 1)
        s2_par = max(s2_pm - s2_vm_within / k, 0.0)
        tot = s2_par + s2_var + s2_run
        return {"s2_parent": s2_par, "s2_variant": s2_var, "s2_run": s2_run,
                "rho_parent": s2_par / tot if tot else float("nan"),
                "r_cross": s2_par / (s2_par + s2_var) if (s2_par + s2_var) else float("nan")}

    pt = comps(tree)
    parents = list(tree); rng = random.Random(seed); bs = []
    for _ in range(B):
        samp = {f"{i}": tree[rng.choice(parents)] for i in range(len(parents))}
        try:
            bs.append(comps(samp))
        except ZeroDivisionError:
            continue
    def ci(key):
        v = sorted(x[key] for x in bs if x[key] == x[key]); return [round(v[int(0.05 * len(v))], 3), round(v[int(0.95 * len(v)) - 1], 3)]
    V = 5
    rc = pt["r_cross"]
    out = {k: round(v, 4) for k, v in pt.items()}
    out.update({"rho_parent_ci90": ci("rho_parent"), "r_cross_ci90": ci("r_cross"),
                "V_eff_of_5": round(V / (1 + (V - 1) * rc), 2) if rc == rc else None})
    return out


def e2(variants_csv, parents_csv):
    Vr = load(variants_csv); Pr = load(parents_csv)
    parents = {str(r["task_id"]).split("-")[0] for r in Vr}
    P = [r for r in Pr if str(r["task_id"]) in parents]
    res = {"variants": rate_summary(Vr), "parents_unperturbed": rate_summary(P),
           "nested_db_mismatch": nested_components(Vr, dbm), "nested_failure": nested_components(Vr, fail)}
    # per variant type vs parent
    types = defaultdict(list)
    for r in Vr:
        types[str(r["task_id"]).split("-", 1)[1]].append(r)
    pf = {t: mean(v) for t, v in by_task(P, fail).items()}
    res["by_variant_type"] = {}
    for t, rows in types.items():
        d = [mean(v) - pf[p.split("-")[0]] for p, v in by_task(rows, fail).items() if p.split("-")[0] in pf]
        res["by_variant_type"][t] = {"runs": len(rows), "failure_rate": round(mean(fail(r) for r in rows), 3),
                                     "mean_diff_vs_parent": round(mean(d), 3) if d else None}
    return res


def e3(csv_path, labels=None):
    rows = attach_labels(load(csv_path), labels)
    out = {"all": rate_summary(rows)}
    for k in ("A", "B", "C"):
        sub = [r for r in rows if str(r["task_id"]).startswith(f"E3{k}")]
        if sub:
            out[f"type_{k}"] = rate_summary(sub)
    if labels:
        nm = sum(int(r.get("lab_near_miss") or 0) for r in rows)
        out["near_miss"] = {"count": nm, "rate": round(nm / len(rows), 4)}
    return out


def omission(r):
    return int(float(r.get("omission_usd") or 0) > 0)


def e1x(cells, B=2000, seed=1):
    """E1x 2 x 3 grid analysis, exactly as pre-registered in EXPERIMENTS.md.

    cells: {(agent, sim): rows} with agent in {"H", "S"} and sim in {"H", "O", "S"}; rows carry lab_* labels.
    Per-task cell rate = mean over its runs. Tasks are resampled jointly across all 6 cells (B = 2,000).
    Sign convention (fixed before any Sonnet-agent outcome was seen): a zero difference has sign 0, and
    "same sign under all three simulators" requires all three strictly negative or all three strictly positive.
    """
    sims = ("H", "O", "S")
    tasks = sorted(set.intersection(*(set(by_task(r, dbm)) for r in cells.values())), key=int)
    out = {"tasks": len(tasks), "cells": {}}
    for (a, c), rows in sorted(cells.items()):
        sm = rate_summary(rows)
        nf = sum(fail(r) for r in rows)
        out["cells"][f"{a}x{c}"] = {"runs": sm["runs"], "db_mismatch": sm["db_mismatch"], "failure": sm["failure"],
                                    "omission_rate": round(mean(omission(r) for r in rows), 4),
                                    "insured_loss": sm["insured_loss"], "attribution": sm["attribution"],
                                    "user_caused_share_of_failures": round(sum(fail(r) and r.get("lab_attribution") == "user_caused"
                                                                               for r in rows) / nf, 3) if nf else None,
                                    "cost_usd": sm["cost_usd"]}

    def sgn(x):
        return (x > 1e-12) - (x < -1e-12)

    def stats(per, idx):
        m = {k: mean(per[k][i] for i in idx) for k in per}
        d = {c: m[("S", c)] - m[("H", c)] for c in sims}
        i_ = {c: d[c] - d["H"] for c in ("O", "S")}
        main = {c: mean(m[(a, c)] - m[(a, "H")] for a in ("H", "S")) for c in ("O", "S")}
        sg = [sgn(d[c]) for c in sims]
        return d, i_, main, (sg[0] != 0 and len(set(sg)) == 1)

    def pct(v):
        v = sorted(v); return [round(v[int(0.05 * len(v))], 4), round(v[int(0.95 * len(v)) - 1], 4)]

    for name, f in (("db_mismatch", dbm), ("failure", fail), ("omission", omission)):
        per = {k: [mean(by_task(rows, f)[t]) for t in tasks] for k, rows in cells.items()}
        d, i_, main, same = stats(per, range(len(tasks)))
        rng = random.Random(seed); bd = defaultdict(list); bi = defaultdict(list); bm = defaultdict(list); bsame = 0
        b_all_neg = b_all_pos = 0
        for _ in range(B):
            idx = [rng.randrange(len(tasks)) for _ in tasks]
            dd, ii, mm, ss = stats(per, idx)
            for c in sims: bd[c].append(dd[c])
            for c in ("O", "S"): bi[c].append(ii[c]); bm[c].append(mm[c])
            bsame += ss; b_all_neg += all(dd[c] < -1e-12 for c in sims); b_all_pos += all(dd[c] > 1e-12 for c in sims)
        res = {"agent_gap": {}, "interaction": {}, "sim_main_effect_avg_over_agents": {}}
        for c in sims:
            diffs = [per[("S", c)][i] - per[("H", c)][i] for i in range(len(tasks))]
            sd = (sum((x - mean(diffs)) ** 2 for x in diffs) / (len(diffs) - 1)) ** 0.5
            ci = pct(bd[c])
            res["agent_gap"][c] = {"delta": round(d[c], 4), "ci90": ci, "excludes_0": ci[0] > 0 or ci[1] < 0,
                                   "mde80": round((Z90 + Z80) * sd / math.sqrt(len(tasks)), 4),
                                   "tasks_to_resolve_point_estimate": (math.ceil(len(tasks) * ((Z90 + Z80) * sd / math.sqrt(len(tasks)) / abs(d[c])) ** 2)
                                                                       if abs(d[c]) > 1e-12 else None)}
        for c in ("O", "S"):
            res["interaction"][c] = {"I": round(i_[c], 4), "ci90": pct(bi[c])}
            res["sim_main_effect_avg_over_agents"][c + "_minus_H"] = {"effect": round(main[c], 4), "ci90": pct(bm[c])}
        signs = {c: sgn(d[c]) for c in sims}
        res["ranking"] = {"point_signs": signs, "same_sign_all_three": same,
                          "boot_p_same_sign": round(bsame / B, 3), "boot_p_all_negative": round(b_all_neg / B, 3),
                          "boot_p_all_positive": round(b_all_pos / B, 3)}
        gaps = res["agent_gap"]
        hard = any(gaps[a]["excludes_0"] and gaps[b]["excludes_0"] and gaps[a]["ci90"][1] < 0 < gaps[b]["ci90"][0]
                   for a in sims for b in sims if a != b)
        soft = (not hard) and len({s for s in signs.values() if s != 0}) > 1
        res["kill"] = {"hard": hard, "soft": soft}
        out[name] = res
    out["primary_outcome"] = "db_mismatch"
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "e1":
        print(json.dumps(e1(*sys.argv[2:5], labels=tuple(sys.argv[5:8]) if len(sys.argv) > 7 else (None, None, None)), indent=1))
    elif cmd == "e2":
        print(json.dumps(e2(sys.argv[2], sys.argv[3]), indent=1))
    elif cmd == "e3":
        print(json.dumps(e3(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), indent=1))
    elif cmd == "e1x":
        # args: six "AxC=runs.csv[:labels.csv]" pairs, e.g. HxH=results/pilot/breadth_runs.csv:results/phase1/e1_H_labels.csv
        cells = {}
        for arg in sys.argv[2:]:
            key, paths = arg.split("=", 1); runs, _, lab = paths.partition(":")
            a, c = key.split("x"); cells[(a, c)] = attach_labels(load(runs), lab or None)
        print(json.dumps(e1x(cells), indent=1))
