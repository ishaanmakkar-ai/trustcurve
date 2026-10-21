"""Premium pipeline unit checks (each could fail)."""

import numpy as np

from trustcurve.study2.forecast import (STRATA, W_DEPLOY, allocation, collapse, concordance, crps_samples, forecast,
                                        interval_score)


def obs(rate_by_stratum, n_per=40, sev=500.0, seed=0, prefix=""):
    rng = np.random.default_rng(seed); out = []
    for h in STRATA:
        for i in range(n_per):
            ev = rng.random() < rate_by_stratum.get(h, 0.0)
            out.append({"task_id": f"{prefix}{h}{i}", "stratum": h, "loss": sev if ev else 0.0})
    return out


def test_allocation_sums_and_follows_mix():
    a = allocation(W_DEPLOY, 200)
    assert sum(a.values()) == 200 and a["cancel"] == 60 and a["other"] == 20


def test_collapse_tasks_are_units_and_cap():
    c = collapse([{"task_id": 1, "stratum": "cancel", "loss": 5000}, {"task_id": 1, "stratum": "cancel", "loss": 0},
                  {"task_id": 2, "stratum": "cancel", "loss": 0}])
    assert len(c["cancel"]) == 2
    t1 = [x for x in c["cancel"] if x[1]][0]
    assert t1[0] == 0.5 and t1[1] == [2000.0]  # capped at the basic limit


def test_point_tracks_truth_and_predictive_mean_matches_theta():
    rates = {"cancel": 0.10, "change": 0.05, "book": 0.05, "compensation": 0.20, "other": 0.02}
    o = {"a": obs(rates, 200, seed=1), "b": obs({h: r / 4 for h, r in rates.items()}, 200, seed=2)}
    for m in ("M1", "M2"):
        f = forecast(o, n_e=400, method=m, B=600, seed=3, config_severity=False)
        truth = sum(W_DEPLOY[h] * rates[h] * 500 for h in STRATA)
        assert abs(f["a"].point - truth) / truth < 0.25
        assert f["a"].point > 2 * f["b"].point  # ranks the riskier configuration higher
        assert abs(np.mean(f["a"].pred_draws) - np.mean(f["a"].theta_draws)) / np.mean(f["a"].theta_draws) < 0.15


def test_zero_events_m1_has_positive_upper_bound():
    o = {"zero": obs({}, 18), "some": obs({"cancel": 0.2}, 18, seed=5)}
    f = forecast(o, n_e=200, method="M1", B=400, seed=1)
    assert f["zero"].point == 0 and f["zero"].hi90 > 0 and f["zero"].pred_hi90 > 0
    assert "zero events" in " ".join(f["zero"].notes)


def test_scores():
    assert interval_score(1, 2, 1.5) == 1
    assert interval_score(1, 2, 3) == 1 + 20 * 1
    assert crps_samples(np.zeros(100), 0.0) == 0
    assert concordance([1, 2, 3], [1, 2, 3]) == 1 and concordance([1, 2, 3], [3, 2, 1]) == 0
