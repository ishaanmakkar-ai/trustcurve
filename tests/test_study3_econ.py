"""Known-truth smoke tests for the Study 3 insurance-economics layer (STUDY3.md §S1)."""

import numpy as np

from trustcurve.study3 import econ


def world(seed=1, n=20, conv=4000):
    rng = np.random.default_rng(seed)
    true = np.exp(rng.normal(0, 1.0, n)) * 2.0                       # true $/conv, 7x spread
    true[:4] = 0.5                                                    # clean controls
    cfgs = [f"c{i}" for i in range(n)]
    losses = {}
    for c, mu in zip(cfgs, true):
        ev = rng.random(conv) < mu / 400.0                            # events with mean severity 400
        losses[c] = np.where(ev, rng.lognormal(np.log(400) - 0.32, 0.8, conv), 0.0)
    cards = {c: {"tier": "mid", "money_tools": True, "human_approval": i % 2 == 0, "guardrail": True} for i, c in enumerate(cfgs)}
    base_model = {c: ("m1" if i % 3 else "m2") for i, c in enumerate(cfgs)}
    perfect = {c: {"point": float(mu), "p75": float(mu) * 1.2} for c, mu in zip(cfgs, true)}
    return cfgs, true, losses, cards, base_model, perfect


def test_perfect_forecaster_lr_equals_plr_rule_i():
    cfgs, true, losses, cards, bm, perfect = world()
    rng = np.random.default_rng(0)
    b = econ.book(econ.premiums(perfect, "i"), losses, econ.boot_means(losses, rng, 500), bm, cfgs[:4])
    assert abs(b["LR"] - econ.PLR) < 0.06                           # realised = expected up to sampling noise


def test_flat_rate_loses_cheapest_quote_market():
    cfgs, true, losses, cards, bm, perfect = world()
    fc, _ = econ.add_outside_in({"F1_3": perfect}, cards)
    rng = np.random.default_rng(0)
    m = econ.market(econ.premiums(fc["F0"]), econ.premiums(perfect), losses, rng)
    assert m["A"]["won_LR"] > m["B"]["won_LR"] + 0.10               # adverse selection against the flat rater
    assert set(m["A"]["won"]) | set(m["B"]["won"]) == set(cfgs)


def test_f0q_revenue_neutral_and_capped():
    cfgs, true, losses, cards, bm, perfect = world()
    fc, mods = econ.add_outside_in({"F1_3": perfect}, cards)
    assert abs(np.mean([fc["F0q"][c]["point"] for c in cfgs]) - fc["F0"][cfgs[0]]["point"]) < 1e-9
    assert all(0.35 <= m <= 3.5 for m in mods.values())


def test_ratios_invariant_to_rescaling():
    cfgs, true, losses, cards, bm, perfect = world()
    k = 0.01
    scaled = {c: x * k for c, x in losses.items()}
    sp = {c: {"point": v["point"] * k, "p75": v["p75"] * k} for c, v in perfect.items()}
    rng = np.random.default_rng(0)
    b1 = econ.book(econ.premiums(perfect), losses, econ.boot_means(losses, rng, 200), bm, cfgs[:4])
    rng = np.random.default_rng(0)
    b2 = econ.book(econ.premiums(sp), scaled, econ.boot_means(scaled, rng, 200), bm, cfgs[:4])
    assert abs(b1["LR"] - b2["LR"]) < 1e-9 and abs(b1["RoC"] - b2["RoC"]) < 1e-9


def test_gap_sign_safe_overpay_risky_underpay():
    cfgs, true, losses, cards, bm, perfect = world()
    fc, _ = econ.add_outside_in({"F1_3": perfect, "F2": perfect}, cards)
    prem = {k: econ.premiums(fc[k], "i") for k in ("F0", "F2")}
    _, agg = econ.not_tested_gap(prem, losses, cfgs[:4])
    assert agg["clean"] > 0 and agg["high"] < 0                       # safe firms overpay; risky firms underpay


def test_f3_lognormal_p75():
    r = econ.f3_from_range(1.0, 0.5, 2.0)
    assert r["point"] == 1.0 and 1.0 < r["p75"] < 2.0


def test_run_all_smoke():
    cfgs, true, losses, cards, bm, perfect = world(conv=1500)
    noisy = {c: {"point": v["point"] * 1.3, "p75": v["p75"] * 1.3} for c, v in perfect.items()}
    econ.B_BOOT = 300
    out = econ.run_all({"F1_3": noisy, "F2": perfect}, losses, cards, bm, cfgs[:4])
    assert set(out["kill"]) == {"KE1", "KE2", "KE3"} and out["kill"]["KE2"] is False
