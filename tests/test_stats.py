import math
from trustcurve.stats import icc_binary, icc_bootstrap, weighted_cluster_size, wilson, zero_event_upper


def test_icc_perfect_clustering_is_one():
    assert icc_binary({"a": [1, 1, 1], "b": [0, 0, 0], "c": [1, 1, 1], "d": [0, 0, 0]}) == 1.0


def test_icc_no_clustering_near_zero_or_negative():
    assert icc_binary({"a": [1, 0], "b": [1, 0], "c": [0, 1], "d": [1, 0]}) < 0


def test_zero_event_upper_matches_rule_of_three():
    assert abs(zero_event_upper(100) - 3 / 100) < 0.002
    assert abs(zero_event_upper(27) - 0.1050) < 0.0005  # review 3 robust bound


def test_weighted_cluster_size():
    assert math.isclose(weighted_cluster_size([5, 5, 5, 3, 3] + [2] * 22), 181 / 65)


def test_wilson_known_value():
    lo, hi = wilson(1, 50)
    assert abs(lo - 0.0035) < 0.001 and abs(hi - 0.105) < 0.001


def test_icc_bootstrap_brackets_point():
    cl = {str(i): ([1, 1] if i % 4 == 0 else [0, 0] if i % 4 == 1 else [1, 0]) for i in range(24)}
    med, lo, hi = icc_bootstrap(cl, B=1000)
    assert lo <= icc_binary(cl) <= hi
