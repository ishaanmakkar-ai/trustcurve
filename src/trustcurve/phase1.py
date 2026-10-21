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
        # Soft (as pre-registered): the point-estimate sign flips "but the CIs overlap". Fixed after review 5 #1:
        # the first version dropped the overlap clause. Fires if some pair with opposite non-zero signs has overlapping CIs.
        def overlap(a, b):
            return gaps[a]["ci90"][0] <= gaps[b]["ci90"][1] and gaps[b]["ci90"][0] <= gaps[a]["ci90"][1]
        flips = [(a, b) for a in sims for b in sims if a < b and signs[a] * signs[b] < 0]
        soft = (not hard) and any(overlap(a, b) for a, b in flips)
        res["kill"] = {"hard": hard, "soft": soft, "sign_flip": bool(flips),
                       "neither_fires_despite_flip": bool(flips) and not hard and not soft}
        out[name] = res
    out["primary_outcome"] = "db_mismatch"
    return out


def _clustered_rate(task_vals):
    """T1 PROP at equal task weights: run-level mean, task-clustered SE (as simstudy2.wmean_se), log 90% interval."""
    ys = [y for v in task_vals for y in v]; n = len(ys); m = sum(ys) / n
    C = len(task_vals)
    z = [sum(y - m for y in v) / n for v in task_vals]
    se = math.sqrt(C / max(C - 1, 1) * sum(x * x for x in z))
    if m <= 0:
        return m, (0.0, 1 - 0.05 ** (1 / C))
    f = math.exp(Z90 * se / m)
    return m, (m / f, m * f)


def _buhlmann_straub(groups):
    """groups: {stratum: [per-task lists of 0/1]} -> {stratum: (raw, credibility)}; same estimator as simstudy2.credibility_fine."""
    keys = list(groups)
    runs = {k: sum(len(v) for v in groups[k]) for k in keys}; tot = {k: sum(sum(v) for v in groups[k]) for k in keys}
    raw = {k: tot[k] / runs[k] for k in keys}
    M = sum(runs.values()); grand = sum(tot.values()) / M
    r = len(groups[keys[0]][0]) if groups[keys[0]] else 2
    epv_num = sum(sum((sum(v) / len(v) - raw[k]) ** 2 for v in groups[k]) * r for k in keys)
    epv_den = sum(len(groups[k]) - 1 for k in keys)
    epv = max(epv_num / max(epv_den, 1), grand * (1 - grand) / r)
    vhm = (sum(runs[k] * (raw[k] - grand) ** 2 for k in keys) - (len(keys) - 1) * epv) / (M - sum(x * x for x in runs.values()) / M)
    vhm = max(vhm, 1e-8)
    return {k: (raw[k], (runs[k] / (runs[k] + epv / vhm)) * raw[k] + (1 - runs[k] / (runs[k] + epv / vhm)) * grand) for k in keys}


def reference(refh_rows, refs_rows, n_slices=200, slice_tasks=25, slice_runs=2, seed=11):
    """Reference-run checks 1-5 as pre-registered in EXPERIMENTS.md (implementation notes there)."""
    from scipy.stats import beta as BETA
    from trustcurve.stats import icc_bootstrap
    rng = random.Random(seed)
    tasks = sorted({r["task_id"] for r in refh_rows}, key=int)
    by = defaultdict(list); strat = {}
    for r in sorted(refh_rows, key=lambda r: int(r["trial"])):
        by[r["task_id"]].append(dbm(r)); strat[r["task_id"]] = r["stratum"]
    truth = mean(mean(by[t]) for t in tasks)
    truth_s = {s: mean(mean(by[t]) for t in tasks if strat[t] == s) for s in set(strat.values())}
    out = {"refh_runs": len(refh_rows), "refh_tasks": len(tasks), "refh_db_mismatch_rate": round(truth, 4),
           "refh_strata": {s: [round(v, 4), sum(strat[t] == s for t in tasks)] for s, v in truth_s.items()}}
    # 1 + 2: small slices
    cov = 0; widths = []; se_raw = []; se_cred = []; zero = 0
    for _ in range(n_slices):
        ts = rng.sample(tasks, slice_tasks)
        vals = {t: rng.sample(by[t], slice_runs) for t in ts}
        m, (lo, hi) = _clustered_rate(list(vals.values()))
        cov += lo <= truth <= hi; widths.append(hi - lo); zero += m == 0
        g = defaultdict(list)
        for t in ts:
            g[strat[t]].append(vals[t])
        bs = _buhlmann_straub(g)
        for s, (rw, cr) in bs.items():
            se_raw.append((rw - truth_s[s]) ** 2); se_cred.append((cr - truth_s[s]) ** 2)
    out["check1_slice_coverage"] = {"slices": n_slices, "cov90": round(cov / n_slices, 3), "pass_0.85_0.95": 0.85 <= cov / n_slices <= 0.95,
                                    "median_width": round(sorted(widths)[len(widths) // 2], 4), "zero_event_slices": zero}
    out["check2_credibility"] = {"mse_raw": round(mean(se_raw), 5), "mse_cred": round(mean(se_cred), 5),
                                 "ratio": round(mean(se_cred) / mean(se_raw), 3), "pass_cred_lt_raw": mean(se_cred) < mean(se_raw)}
    # 3: clustering
    fb = defaultdict(list)
    for r in refh_rows:
        fb[r["task_id"]].append(fail(r))
    out["check3_icc"] = {"db_mismatch": [round(x, 3) for x in (icc_binary(by),) + icc_bootstrap(by, B=2000)],
                         "failure": [round(x, 3) for x in (icc_binary(fb),) + icc_bootstrap(fb, B=2000)],
                         "format": "[point, boot median, 2.5%, 97.5%]", "pilot_db_mismatch": 0.42,
                         "pass_0.3_0.6": 0.3 <= icc_binary(by) <= 0.6}
    # 4: simulator effect at scale (same 25 tasks)
    s_tasks = {r["task_id"] for r in refs_rows}
    hsub = [r for r in refh_rows if r["task_id"] in s_tasks]
    out["check4_sim_effect_S_minus_H"] = {"failure": paired(hsub, refs_rows, fail), "db_mismatch": paired(hsub, refs_rows, dbm),
                                         "refs_summary": rate_summary(refs_rows)}
    # 5: insured loss on REF-H
    x = sum(insured(r) for r in refh_rows); n = len(refh_rows); T = len(tasks)
    xe = x / n * T
    cp_tasks = (1 - 0.05 ** (1 / T)) if x == 0 else float(BETA.ppf(0.95, xe + 1, T - xe))
    out["check5_insured"] = {"events": x, "runs": n, "rate": round(x / n, 5), "wilson90": [round(v, 5) for v in wilson(x, n, Z90)],
                             "cp_on_tasks_upper95": round(cp_tasks, 4), "tasks_with_event": len({r["task_id"] for r in refh_rows if insured(r)}),
                             "pass_le_2pct": x / n <= 0.02}
    out["refh_summary"] = rate_summary(refh_rows)
    return out


def sign_test(a_rows, b_rows, f):
    """Exact two-sided sign test on per-task differences (b - a) of mean outcome; ties dropped.
    Added after review 5 (post-hoc robustness check, not a pre-registered test)."""
    A, Bt = by_task(a_rows, f), by_task(b_rows, f)
    d = [mean(Bt[t]) - mean(A[t]) for t in sorted(set(A) & set(Bt))]
    pos = sum(x > 0 for x in d); neg = sum(x < 0 for x in d); n = pos + neg
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(pos, neg) + 1)) / 2 ** n) if n else 1.0
    return {"pos": pos, "neg": neg, "ties": len(d) - n, "p_two_sided": round(p, 4)}


def mcnemar_majority(a_rows, b_rows, f):
    """Exact McNemar on task-level majority outcomes (mean >= 0.5), as pre-registered for E1."""
    A, Bt = by_task(a_rows, f), by_task(b_rows, f)
    ts = sorted(set(A) & set(Bt))
    a_only = sum(mean(A[t]) >= 0.5 and mean(Bt[t]) < 0.5 for t in ts)
    b_only = sum(mean(Bt[t]) >= 0.5 and mean(A[t]) < 0.5 for t in ts)
    n = a_only + b_only
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a_only, b_only) + 1)) / 2 ** n) if n else 1.0
    return {"a_only": a_only, "b_only": b_only, "p_exact": round(p, 4)}


def sign_test_diffs(d):
    pos = sum(x > 1e-12 for x in d); neg = sum(x < -1e-12 for x in d); n = pos + neg
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(pos, neg) + 1)) / 2 ** n) if n else 1.0
    return {"pos": pos, "neg": neg, "ties": len(d) - n, "p_two_sided": round(p, 4)}


def cluster_ci(rows, f, key=lambda r: str(r["task_id"]), B=2000, seed=1):
    """Cluster (task or parent) bootstrap 90% percentile interval for a run-level rate."""
    g = defaultdict(list)
    for r in rows:
        g[key(r)].append(f(r))
    ks = list(g); rng = random.Random(seed); bs = []
    for _ in range(B):
        ys = [y for _ in ks for y in g[ks[rng.randrange(len(ks))]]]
        bs.append(sum(ys) / len(ys))
    bs.sort()
    return [round(bs[int(0.05 * B)], 4), round(bs[int(0.95 * B) - 1], 4)]


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "e1":
        print(json.dumps(e1(*sys.argv[2:5], labels=tuple(sys.argv[5:8]) if len(sys.argv) > 7 else (None, None, None)), indent=1))
    elif cmd == "e2":
        print(json.dumps(e2(sys.argv[2], sys.argv[3]), indent=1))
    elif cmd == "e3":
        print(json.dumps(e3(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), indent=1))
    elif cmd == "reference":
        print(json.dumps(reference(load(sys.argv[2]), load(sys.argv[3])), indent=1))
    elif cmd == "e1x":
        # args: six "AxC=runs.csv[:labels.csv]" pairs, e.g. HxH=results/pilot/breadth_runs.csv:results/phase1/e1_H_labels.csv
        cells = {}
        for arg in sys.argv[2:]:
            key, paths = arg.split("=", 1); runs, _, lab = paths.partition(":")
            a, c = key.split("x"); cells[(a, c)] = attach_labels(load(runs), lab or None)
        print(json.dumps(e1x(cells), indent=1))
