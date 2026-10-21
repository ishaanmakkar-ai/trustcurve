import random

from trustcurve.phase1 import _buhlmann_straub, _clustered_rate, reference


def fake(tasks, runs, p_of, sim="h", seed=0):
    rng = random.Random(seed); out = []
    for t in tasks:
        for k in range(runs):
            bad = rng.random() < p_of(t)
            out.append({"task_id": str(t), "trial": str(k), "reward": "0.0" if bad else "1.0", "db_match": "False" if bad else "True",
                        "stratum": ["cancel", "book", "change"][t % 3], "insured_loss_event": "False", "omission_usd": "0",
                        "cost_usd_from_tokens": "0.01"})
    return out


def test_clustered_rate_zero_uses_cp_fallback():
    m, (lo, hi) = _clustered_rate([[0, 0]] * 25)
    assert m == 0 and lo == 0 and abs(hi - (1 - 0.05 ** (1 / 25))) < 1e-12


def test_credibility_shrinks_toward_grand_mean():
    g = {"a": [[1, 1], [0, 0]], "b": [[0, 0], [0, 0], [0, 0]]}
    bs = _buhlmann_straub(g)
    grand = 2 / 10
    assert bs["a"][0] == 0.5 and grand <= bs["a"][1] <= 0.5 and 0 <= bs["b"][1] <= grand


def test_reference_runs_end_to_end_and_covers():
    p = lambda t: [0.0, 0.05, 0.6][t % 3] if t % 5 else 0.9
    H = fake(range(50), 20, p); S = fake(range(25), 20, p, seed=1)
    r = reference(H, S, n_slices=200)
    assert r["refh_tasks"] == 50 and 0.75 <= r["check1_slice_coverage"]["cov90"] <= 1.0
    assert r["check5_insured"]["events"] == 0 and r["check5_insured"]["cp_on_tasks_upper95"] > 0.05
    assert abs(r["check4_sim_effect_S_minus_H"]["db_mismatch"]["mean_diff"]) < 0.1
