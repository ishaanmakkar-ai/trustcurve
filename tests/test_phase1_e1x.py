from trustcurve.phase1 import e1x


def rows(rates):
    """rates: per-task number of DB mismatches out of 2 runs."""
    out = []
    for t, k in enumerate(rates):
        for trial in range(2):
            bad = trial < k
            out.append({"task_id": str(t), "trial": str(trial), "reward": "0.0" if bad else "1.0",
                        "db_match": "False" if bad else "True", "omission_usd": "0", "insured_loss_event": "False",
                        "cost_usd_from_tokens": "0.01", "lab_attribution": "agent_caused" if bad else ""})
    return out


def test_no_gap_gives_zero_delta_and_no_kill():
    base = [0, 1, 2, 0, 0, 1, 0, 2, 0, 0] * 2
    cells = {(a, c): rows(base) for a in "HS" for c in "HOS"}
    r = e1x(cells, B=200)["db_mismatch"]
    assert all(g["delta"] == 0 for g in r["agent_gap"].values())
    assert r["kill"] == {"hard": False, "soft": False} and r["ranking"]["boot_p_same_sign"] == 0


def test_opposite_significant_gaps_fire_hard_kill():
    n = 30
    hi, lo = [2] * n, [0] * n
    cells = {("H", "H"): rows(hi), ("S", "H"): rows(lo),    # Sonnet better under H
             ("H", "O"): rows(lo), ("S", "O"): rows(hi),    # Sonnet worse under O
             ("H", "S"): rows(hi), ("S", "S"): rows(lo)}
    r = e1x(cells, B=200)["db_mismatch"]
    assert r["agent_gap"]["H"]["delta"] == -1 and r["agent_gap"]["O"]["delta"] == 1
    assert r["interaction"]["O"]["I"] == 2
    assert r["kill"]["hard"] and not r["kill"]["soft"]


def test_sign_flip_with_overlapping_cis_is_soft():
    a = [1, 0, 0, 0, 1, 0, 0, 0, 0, 0] * 2
    b = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0] * 2
    cells = {("H", "H"): rows(a), ("S", "H"): rows(b), ("H", "O"): rows(b), ("S", "O"): rows(a),
             ("H", "S"): rows(a), ("S", "S"): rows(b)}
    r = e1x(cells, B=500)["db_mismatch"]
    assert r["ranking"]["point_signs"] == {"H": -1, "O": 1, "S": -1}
    assert r["kill"] == {"hard": False, "soft": True}
