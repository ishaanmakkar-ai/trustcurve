"""C′ pipeline on synthetic runs (no API calls): loss assembly, detection, forecasts."""

import random

from trustcurve.study3.pipeline import assemble, detection, forecasts

W = {"cancel": 0.26, "change": 0.27, "book": 0.14, "compensation": 0.17, "other": 0.16}
STR = list(W)


def synth(rate_by_cfg, n_tasks=60, trials=3, seed=1):
    rng = random.Random(seed); rows, st = [], {}
    for c, p in rate_by_cfg.items():
        for t in range(n_tasks):
            for k in range(trials):
                ev = rng.random() < p
                rows.append({"config": c, "task_id": f"T{t}", "trial": str(k), "stratum": STR[t % 5],
                             "commission_usd": 300.0 if ev else 0.0, "commission_event": str(ev), "harm_usd": 0.0,
                             "harm_event": "False", "failed": str(ev), "error": ""})
                st[(c, f"T{t}", str(k))] = {"statement_usd": 0.0, "any_misstatement": False}
    return rows, st


def test_detection_flags_a_clearly_worse_config_and_not_a_clone():
    rows, st = synth({"C0": 0.01, "C1": 0.01, "X1": 0.3})
    det = detection(assemble(rows, st, include_statement=True))
    assert det["X1"]["flag_primary"] and not det["C1"]["flag_primary"]


def test_statement_missing_and_exclusion():
    rows, st = synth({"C0": 0.0})
    st[("C0", "T0", "0")] = {"statement_usd": 500.0, "any_misstatement": True}
    del st[("C0", "T1", "0")]
    recs = assemble(rows, st, include_statement=True)["C0"]
    r0 = next(r for r in recs if r["task_id"] == "T0" and r["trial"] == "0")
    r1 = next(r for r in recs if r["task_id"] == "T1" and r["trial"] == "0")
    assert r0["loss"] == 500 and r0["event"] and r1["statement_missing"]
    recs2 = assemble(rows, st, include_statement=False)["C0"]
    assert next(r for r in recs2 if r["task_id"] == "T0" and r["trial"] == "0")["loss"] == 0


def test_forecasts_order_and_subset():
    rows, st = synth({"C0": 0.01, "X1": 0.2, "X2": 0.05})
    recs = assemble(rows, st, include_statement=True)
    f = forecasts(recs, W, B=500)
    assert f["X1"]["point"] > f["X2"]["point"] > 0 and f["X1"]["p75"] >= f["X1"]["lo90"]
    sub = forecasts(recs, W, tasks={f"T{i}" for i in range(20)}, B=500)
    assert sub["X1"]["n_tasks"] < f["X1"]["n_tasks"]


def test_freeze_all_synthetic():
    from trustcurve.study3.configs import CONFIGS3
    from trustcurve.study3.pipeline import freeze_all
    rates = {c: (0.25 if c.startswith(("D", "X")) else 0.01) for c in CONFIGS3}
    f1_rows, st1 = synth(rates, n_tasks=30, seed=2)
    f2_rows, st2 = synth(rates, n_tasks=40, seed=3)
    cards = {c: CONFIGS3[c].card for c in CONFIGS3}
    out = freeze_all(f1_rows, f2_rows, {**st1, **st2}, True, W, {f"T{i}" for i in range(20)}, cards,
                     f3_rows=[{"agent": "Agent 01", "total_per_1000_usd": "500", "total_low_90_usd": "100",
                               "total_high_90_usd": "2000"}], card_map={"Agent 01": "C0"})
    fc = out["forecasts"]
    assert set(fc) >= {"F1_3", "F1_1", "F2", "F2p", "F0", "F0q", "F3"}
    assert fc["F1_3"]["X1"]["point"] > fc["F1_3"]["C1"]["point"] and fc["F3"]["C0"]["point"] == 0.5
    assert out["detection"]["F2"]["X1"]["flag_primary"] and len({round(v["point"], 9) for v in fc["F0"].values()}) == 1
