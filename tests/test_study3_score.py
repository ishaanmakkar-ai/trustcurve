"""C′ scoring on a synthetic frozen state (no API calls)."""

import random

from trustcurve.study3.configs import CONFIGS3
from trustcurve.study3.score import score_all


def test_score_all_synthetic():
    rng = random.Random(4)
    true = {c: (2.0 + 10 * rng.random() if v.source != "clean" else 0.3) for c, v in CONFIGS3.items()}
    good = {c: {"point": t * rng.uniform(0.8, 1.25), "p75": t * 1.4, "lo90": t * 0.5, "hi90": t * 2} for c, t in true.items()}
    flat = {c: {"point": 5.0, "p75": 6.0, "lo90": 1.0, "hi90": 10.0} for c in true}
    det = {b: {c: {"flag_primary": (v.source != "clean") if b == "F2" else (v.source == "designed"),
                   "flag_fail": False, "flag_any": False} for c, v in CONFIGS3.items() if c != "C0"} for b in ("F2", "F1_3", "F1_1")}
    frozen = {"forecasts": {"F2": good, "F1_3": flat, "F1_1": flat, "F0": flat}, "detection": det}
    exp = {c: [{"loss": t * rng.uniform(0.7, 1.3)} for _ in range(20)] for c, t in true.items()}
    s = score_all(frozen, exp)
    assert s["pricing"]["F2"]["medlog"] < s["pricing"]["F1_3"]["medlog"] and s["h3"]["H3b"]
    assert s["rq1"]["H2"] and s["rq1"]["H1"] and s["rq1"]["mcnemar_F2_vs_F1_3"]["b"] > 0
    assert s["pricing"]["F2"]["coverage"] > 0.8
