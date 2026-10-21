import math
import numpy as np
from trustcurve.simstudy import Scenario, draw_sample, est_is, est_naive, BENCH, IS_MIX


def test_truth_calibrates_to_target():
    for q in (0.02, 0.05):
        assert abs(Scenario(q, 0.3, 0.9).truth()["rate"] - q) < 0.002


def test_importance_sampling_unbiased_at_large_n_and_naive_biased():
    sc = Scenario(0.05, 0.3, 0.5); mu = sc.mu(); t = sc.truth()["rate"]; rng = np.random.default_rng(3)
    is_est = np.mean([est_is(draw_sample(sc, mu, IS_MIX, 20000, rng))[0] for _ in range(20)])
    nv_est = np.mean([est_naive(draw_sample(sc, mu, BENCH, 20000, rng))[0] for _ in range(20)])
    assert abs(is_est / t - 1) < 0.03
    assert nv_est / t - 1 < -0.08  # benchmark mix under-weights risky strata


def test_parent_clustering_wider_than_variant_clustering():
    sc = Scenario(0.05, 0.6, 0.9); mu = sc.mu(); s = draw_sample(sc, mu, IS_MIX, 4000, np.random.default_rng(5))
    assert est_is(s, "par")[1] > est_is(s, "var")[1]


def test_zero_event_fallback_gives_cp_upper_on_parents():
    from trustcurve.simstudy2 import interval
    lo, hi = interval(0.0, 0.0, 30)
    assert lo == 0.0 and abs(hi - (1 - 0.05 ** (1 / 30))) < 1e-12
