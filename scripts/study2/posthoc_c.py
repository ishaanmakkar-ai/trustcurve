"""Phase C POST-HOC analyses after review 8 (labelled; the frozen primary result is unchanged).

1. Within-group headlines: pre13 (K2 set) and the 11 added configurations ("ext11"); plus an indicator baseline
   (group membership alone as the forecast) for the pooled 24.
2. Bootstrap CIs that resample each configuration's own experience tasks (paired where tasks are shared).
3. Factor contrasts vs B0 on shared tasks with Holm correction (sign tests), CI and p reported together.
4. Same-task comparisons for small-n configurations (KB-CAPS vs KNO-WR; CAP-S, INT-2 vs B0 on the first 50 tasks).
5. Simulator bridge: task-paired event counts H vs S vs L (sign tests over configuration x task cells).
6. Guardrail net of omission (KB-HPC, KB-HCF vs KNO-WR; HAR-* vs B0).
7. Ledger repricing variants: (a) flown-segment cancellations priced at the flown segments' value only;
   (b) booking_on_other_account moved to a separate customer-harm peril.

Usage: python scripts/study2/posthoc_c.py <out.json>
"""

from __future__ import annotations

import csv
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from trustcurve.study2.forecast import spearman  # noqa: E402

F = json.load(open(ROOT / "results/study2/forecasts_frozen.json"))["configs"]
SIMS = ("S", "L")


def load_rows():
    rows = []
    for f in glob.glob(str(ROOT / "results/study2/runs/exp-*.csv")):
        rows += [r for r in csv.DictReader(open(f)) if not r.get("error")]
    return rows


def per_task(rows, col="commission_usd", sims=SIMS):
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["sim"] in sims:
            acc[r["config"]][r["task_id"]].append(float(r[col] or 0))
    return {c: {t: float(np.mean(v)) for t, v in d.items()} for c, d in acc.items()}


def realised(tm):
    return {c: float(np.mean(list(d.values()))) for c, d in tm.items()}


def group_stats(cfgs, tm, key="combined", B=2000, seed=1):
    R = realised(tm); cs = [c for c in cfgs if c in R]
    pts = np.array([F[c][key]["point"] for c in cs]); ys = np.array([R[c] for c in cs])
    cov = [F[c][key]["pred_lo90"] - 1e-9 <= R[c] <= F[c][key]["pred_hi90"] + 1e-9 for c in cs]
    # bootstrap: resample each configuration's own tasks; shared tasks get the same draw (paired via task index map)
    rng = np.random.default_rng(seed); alltasks = sorted({t for c in cs for t in tm[c]})
    idx = {t: i for i, t in enumerate(alltasks)}; bs = []
    for _ in range(B):
        w = rng.poisson(1.0, len(alltasks))  # Poisson bootstrap weights per task, shared across configurations
        yb = []
        for c in cs:
            ts = list(tm[c]); ww = np.array([w[idx[t]] for t in ts], float); vv = np.array([tm[c][t] for t in ts])
            yb.append(float((ww * vv).sum() / ww.sum()) if ww.sum() > 0 else float(vv.mean()))
        s = spearman(pts, np.array(yb))
        if s == s:
            bs.append(s)
    return {"n": len(cs), "spearman": spearman(pts, ys), "spearman_ci90_own_tasks_poisson_bootstrap":
            [float(np.quantile(bs, 0.05)), float(np.quantile(bs, 0.95))] if bs else None,
            "coverage": float(np.mean(cov)), "covered": dict(zip(cs, map(bool, cov))),
            "forecast_over_realised": {c: (F[c][key]["point"] / R[c]) if R[c] > 0 else None for c in cs}}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [None] * len(ps); m = len(ps); run = 0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * ps[i])); adj[i] = run
    return adj


def contrasts(tm, base="B0"):
    out = {}; names = [c for c in sorted(tm) if c != base]; ps = []
    for c in names:
        ts = sorted(set(tm[c]) & set(tm[base]))
        a = np.array([tm[c][t] for t in ts]); b = np.array([tm[base][t] for t in ts])
        pos, neg = int((a > b).sum()), int((a < b).sum())
        p = float(sps.binomtest(pos, pos + neg).pvalue) if pos + neg else 1.0
        rng = np.random.default_rng(3); ix = rng.integers(0, len(ts), (2000, len(ts)))
        d = a[ix].mean(1) - b[ix].mean(1)
        out[c] = {"n_tasks": len(ts), "diff": float(a.mean() - b.mean()),
                  "diff_ci90": [float(np.quantile(d, .05)), float(np.quantile(d, .95))],
                  "tasks_higher_lower": [pos, neg], "p_sign": p, "event_tasks": int(((a > 0) | (b > 0)).sum())}
        ps.append(p)
    for c, pa in zip(names, holm(ps)):
        out[c]["p_holm"] = pa
    return out


def shared(tm, a, b, n_first=None):
    ts = sorted(set(tm[a]) & set(tm[b]))
    return {"n_tasks": len(ts), a: float(np.mean([tm[a][t] for t in ts])), b: float(np.mean([tm[b][t] for t in ts]))}


def bridge_test(rows):
    ev = defaultdict(dict)
    for r in rows:
        ev[(r["config"], r["task_id"])][r["sim"]] = r["commission_event"] == "True"
    cells = [v for v in ev.values() if all(s in v for s in ("H", "S", "L"))]
    out = {"cells": len(cells), "events": {s: int(sum(v[s] for v in cells)) for s in ("H", "S", "L")}}
    for x, y in (("H", "S"), ("H", "L"), ("S", "L")):
        a = sum(1 for v in cells if v[x] and not v[y]); b = sum(1 for v in cells if v[y] and not v[x])
        out[f"{x}_vs_{y}_discordant"] = [a, b]
        out[f"{x}_vs_{y}_p_mcnemar_exact"] = float(sps.binomtest(a, a + b).pvalue) if a + b else 1.0
    return out


def reprice(rows):
    """Variant ledger pricing on commission-event runs: flown-segment cancellations at the flown value only;
    booking_on_other_account removed (separate customer-harm peril)."""
    from loguru import logger
    logger.remove()
    from tau2.data_model.tasks import Task
    from trustcurve.study2.ledger import FLOWN, _db, _fresh_env, executed_calls, _status
    meta = json.load(open(ROOT / "tasks/study2/experience_main/meta.json"))
    cache = {}; changed = 0
    out = []
    for r in rows:
        r = dict(r)
        if r["commission_event"] == "True" and ("wrongful_cancellation_refund" in r["ledger_kinds"]
                                                or "booking_on_other_account" in r["ledger_kinds"]):
            key = (r["config"], r["sim"])
            if key not in cache:
                d = json.load(open(ROOT / f"results/raw/study2/exp-{r['config']}-{r['sim']}/results.json"))
                cache[key] = ({str(s["task_id"]): s for s in d["simulations"]}, {str(t["id"]): t for t in d["tasks"]})
            sims, tasks = cache[key]; s = sims[r["task_id"]]; task = Task.model_validate(tasks[r["task_id"]])
            init = _db(_fresh_env(task)); loss = 0.0
            for name, args in executed_calls(s["messages"]):
                if name == "cancel_reservation":
                    res = init["reservations"].get(args.get("reservation_id"))
                    if res and any(_status(init, f["flight_number"], f["date"]) in FLOWN for f in res["flights"]):
                        pax = len(res["passengers"])
                        loss += sum(f["price"] for f in res["flights"]
                                    if _status(init, f["flight_number"], f["date"]) in FLOWN) * pax
            orig = float(r["commission_usd"])
            flown_items = loss > 0
            if flown_items or "booking_on_other_account" in r["ledger_kinds"]:
                new = orig
                if flown_items:
                    new = min(orig, loss)
                if "booking_on_other_account" in r["ledger_kinds"] and r["ledger_kinds"] == "booking_on_other_account":
                    new = 0.0
                if abs(new - orig) > 1e-6:
                    changed += 1
                r["commission_usd"] = str(new); r["commission_event"] = str(new > 0)
        out.append(r)
    return out, changed


def main(out_path):
    rows = load_rows(); tm = per_task(rows)
    pre13 = [c for c in F if F[c]["group"] == "pre13"]; ext11 = [c for c in F if F[c]["group"] == "extended"]
    res = {"LABEL": "POST-HOC (review 8); the frozen primary result in score_c.json is unchanged"}
    res["pre13"] = group_stats(pre13, tm); res["ext11"] = group_stats(ext11, tm)
    res["all24_forecast"] = group_stats(list(F), tm)
    R = realised(tm); cs = [c for c in F if c in R]
    ind = np.array([1.0 if F[c]["group"] == "extended" else 0.0 for c in cs])
    res["all24_indicator_baseline_spearman"] = spearman(ind, np.array([R[c] for c in cs]))
    res["factor_contrasts_holm"] = contrasts(tm)
    res["shared_task_comparisons"] = {"KB-CAPS_vs_KNO-WR": shared(tm, "KB-CAPS", "KNO-WR"),
                                      "CAP-S_vs_B0": shared(tm, "CAP-S", "B0"), "INT-2_vs_B0": shared(tm, "INT-2", "B0"),
                                      "KB-HPC_vs_KNO-WR": shared(tm, "KB-HPC", "KNO-WR"),
                                      "KB-HCF_vs_KNO-WR": shared(tm, "KB-HCF", "KNO-WR")}
    om = per_task(rows, "omission_usd"); Ro = realised(om)
    res["guardrail_net_of_omission"] = {c: {"commission": R.get(c), "omission": Ro.get(c),
                                            "total": (R.get(c) or 0) + (Ro.get(c) or 0)}
                                        for c in ("B0", "HAR-PC", "HAR-CF", "KNO-WR", "KB-HPC", "KB-HCF")}
    res["bridge_paired_events"] = bridge_test(rows)
    rp, changed = reprice(rows); tmr = per_task(rp)
    res["reprice_flown_and_harm"] = {"runs_changed": changed, "pre13": group_stats(pre13, tmr, B=500),
                                     "ext11": group_stats(ext11, tmr, B=500),
                                     "realised": {c: round(v, 2) for c, v in sorted(realised(tmr).items(), key=lambda kv: -kv[1])}}
    ev_tasks = defaultdict(set)
    for r in rows:
        if r["sim"] in SIMS and r["commission_event"] == "True":
            ev_tasks[F[r["config"]]["group"]].add(r["task_id"])
    res["distinct_event_tasks"] = {g: len(v) for g, v in ev_tasks.items()}
    Path(out_path).write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({k: (res[k]["spearman"], res[k]["coverage"]) for k in ("pre13", "ext11", "all24_forecast")}),
          "indicator", res["all24_indicator_baseline_spearman"])


if __name__ == "__main__":
    main(sys.argv[1])
