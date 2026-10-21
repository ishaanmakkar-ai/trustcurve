"""Phase C scoring on synthetic inputs where the answer is known (no API calls)."""

import csv
import json

import numpy as np

from trustcurve.study2 import score_c


def _write(tmp_path, rates, n_tasks=60, sims=("H", "O"), seed=0):
    rng = np.random.default_rng(seed); rows = []
    for c, p in rates.items():
        for s in sims:
            for t in range(n_tasks):
                ev = rng.random() < p
                rows.append({"config": c, "sim": s, "task_id": f"t{t}", "trial": 0, "commission_usd": 300.0 if ev else 0.0,
                             "commission_event": str(ev), "omission_usd": 0.0, "error": ""})
    path = tmp_path / "runs.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return path


def _fc(rates, width=0.6):
    out = {}
    for c, p in rates.items():
        mu = 300 * p
        draws = list(np.random.default_rng(1).gamma(4, mu / 4 + 1e-9, 400))
        f = {"point": mu, "pred_lo90": float(np.quantile(draws, 0.05)), "pred_hi90": float(np.quantile(draws, 0.95)),
             "pred_hi95": float(np.quantile(draws, 0.95)), "pred_draws": draws}
        out[c] = {"combined": f, "single": f}
    return {"configs": out}


def test_perfect_ranking_and_k2(tmp_path):
    rates = {"B0": 0.02, "PER-PL": 0.10, "KNO-RM": 0.06, "HAR-PC": 0.01, "INT-1": 0.25, "CAP-S": 0.015}
    runs = _write(tmp_path, rates, n_tasks=400)
    fc = tmp_path / "fc.json"; fc.write_text(json.dumps(_fc(rates)))
    out = tmp_path / "out.json"
    score_c.main(str(fc), str(out), [str(runs)])
    r = json.loads(out.read_text())
    assert r["primary"]["rq1"]["spearman"] > 0.8
    assert r["primary"]["k2"]["K2_fires"] is False
    fe = r["rq3_factor_effects"]
    assert fe["PER-PL"]["diff"] > 0 and fe["PER-PL"]["diff_ci90"][0] > 0
    assert "INT-1" in r["rq3_interactions"]
    assert set(r["rq5_by_simulator"]) == {"H", "O"}


def test_reversed_ranking_fires_k2(tmp_path):
    rates = {"B0": 0.02, "PER-PL": 0.10, "KNO-RM": 0.06, "HAR-PC": 0.01, "INT-1": 0.25}
    runs = _write(tmp_path, rates, n_tasks=400)
    wrong = {c: rates[k] for c, k in zip(rates, reversed(list(rates)))}
    fc = tmp_path / "fc.json"; fc.write_text(json.dumps(_fc(wrong)))
    out = tmp_path / "out.json"
    score_c.main(str(fc), str(out), [str(runs)])
    assert json.loads(out.read_text())["primary"]["k2"]["K2_fires"] is True


def test_all_zero_realised_fires_k2_undetermined(tmp_path):
    """Review 6 #6: with no realised events, Spearman is NaN and coverage is trivially met; K2 must not pass."""
    rates = {"B0": 0.0, "PER-PL": 0.0, "KNO-RM": 0.0, "HAR-PC": 0.0, "INT-1": 0.0}
    runs = _write(tmp_path, rates, n_tasks=100)
    fc = tmp_path / "fc.json"; fc.write_text(json.dumps(_fc({c: r + 0.01 for c, r in rates.items()})))
    out = tmp_path / "out.json"
    score_c.main(str(fc), str(out), [str(runs)])
    k = json.loads(out.read_text())["primary"]["k2"]
    assert k["K2_fires"] is True and k["spearman_undetermined"] is True
