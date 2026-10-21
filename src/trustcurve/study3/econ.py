"""Study 3 insurance-economics layer (pre-registered in STUDY3.md §S1, commit ae2d5b4). Pure computation, $0.

Inputs (built from the frozen forecasts and the experience results; nothing here reads the sealed catalogues):
  forecasts : {forecaster: {cfg: {"point": $/conv, "p75": $/conv}}}   (F3: {"median", "lo90", "hi90"} -> lognormal p75)
  losses    : {cfg: np.ndarray of realised $ per experience conversation (all perils)}
  cards     : {cfg: {"tier": "frontier"|"mid"|"small", "money_tools": bool, "human_approval": bool, "guardrail": bool}}
  base_model: {cfg: model id}
  clean     : list of clean-control cfg ids
"""

from __future__ import annotations

import numpy as np

PLR, PLR_SWEEP = 0.60, (0.50, 0.55, 0.60, 0.65)
EXPENSE, INV_INCOME, COST_EQUITY, CAP_FLOOR, CR_TARGET = 0.37, 0.025, 0.10, 1.0, 0.95
V, V_SWEEP = 10_000_000, (1_000_000, 10_000_000, 30_000_000)
BETA, LAPSE = 5.0, (0.0, 0.3)
B_BOOT = 10_000
SAVING, SAVING_RANGE, RESOLUTION = 4.0, (3.0, 6.0), 0.51
FREQ_SWEEP = (0.0001, 0.001, 0.01)
Z75 = 0.6744897501960817
Z95 = 1.6448536269514722
CARD_MOD = {"tier": {"frontier": 0.9, "mid": 1.0, "small": 1.1},
            "money_tools": {True: 1.1, False: 0.9}, "human_approval": {True: 0.9, False: 1.1},
            "guardrail": {True: 0.9, False: 1.0}}


def f3_from_range(median, lo90, hi90):
    """Lognormal through the median with sigma from the 90% range; returns point (median) and p75."""
    sig = (np.log(max(hi90, 1e-9)) - np.log(max(lo90, 1e-9))) / (2 * Z95)
    return {"point": float(median), "p75": float(median * np.exp(Z75 * sig))}


def add_outside_in(forecasts, cards, anchor="F1_3"):
    """E0: F0 = book-mean of the anchor's points (and p75s); F0q = F0 x card modifier / mean(modifier)."""
    a = forecasts[anchor]; cfgs = list(a)
    pt, p75 = float(np.mean([a[c]["point"] for c in cfgs])), float(np.mean([a[c]["p75"] for c in cfgs]))
    out = dict(forecasts)
    out["F0"] = {c: {"point": pt, "p75": p75} for c in cfgs}
    m = {c: float(np.clip(np.prod([CARD_MOD[k][cards[c][k]] for k in CARD_MOD]), 0.35, 3.5)) for c in cfgs}
    mbar = float(np.mean(list(m.values())))
    out["F0q"] = {c: {"point": pt * m[c] / mbar, "p75": p75 * m[c] / mbar} for c in cfgs}
    return out, m


def premiums(fc, rule="ii", plr=PLR):
    key = "point" if rule == "i" else "p75"
    return {c: v[key] / plr for c, v in fc.items()}


def boot_means(losses, rng, B=None):
    """Bootstrap distribution of each insured's mean $/conversation (resample conversations)."""
    B = B or B_BOOT
    return {c: np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)]) for c, x in losses.items()}


def correlated_excess(losses, base_model, clean):
    """Correlated-flaw scenario (S1 E2): largest realised excess $/conv among flawed configurations on the modal base
    model, applied to every insured on that model."""
    clean_mean = float(np.mean([losses[c].mean() for c in clean]))
    models = [base_model[c] for c in losses]
    modal = max(set(models), key=models.count)
    on = [c for c in losses if base_model[c] == modal]
    exc = max(max(losses[c].mean() - clean_mean, 0.0) for c in on if c not in clean) if any(c not in clean for c in on) else 0.0
    return modal, on, exc


def book(prem, losses, boots, base_model, clean, v=V, insureds=None):
    """E2 for one forecaster's premiums over a set of insureds (default: all)."""
    ins = list(insureds if insureds is not None else prem)
    if not ins:
        return {"n": 0}
    P = sum(prem[c] for c in ins) * v
    EL = sum(losses[c].mean() for c in ins) * v
    lr = EL / P
    sim = np.sum([boots[c] for c in ins], axis=0) * v
    q995 = float(np.quantile(sim, 0.995))
    modal, on, exc = correlated_excess(losses, base_model, clean)
    corr = EL + exc * v * len([c for c in ins if c in on])
    tail = max(q995, corr)
    cap = max(CAP_FLOOR * P, tail - EL)
    uw = P * (1 - EXPENSE) - EL
    roc = (uw + INV_INCOME * P) / cap
    return {"n": len(ins), "premium": P, "expected_loss": EL, "LR": lr, "CR": lr + EXPENSE, "uw_profit": uw,
            "q995_book": q995, "correlated_scenario": corr, "capital": cap, "RoC": roc,
            "profitable": bool(lr + EXPENSE <= CR_TARGET and roc >= COST_EQUITY),
            "LR_by_config": {c: losses[c].mean() / prem[c] for c in ins}}


def market(prem_a, prem_b, losses, rng, beta=None, lapse=0.0):
    """E3: each insured buys the cheaper quote (beta None) or switches by logit; informed buyers whose realised loss
    is < 50% of their premium lapse with probability `lapse`. Returns won sets (fractional weights for logit)."""
    w = {"A": {}, "B": {}}
    for c in prem_a:
        if beta is None:
            pa = 1.0 if prem_a[c] < prem_b[c] else (0.5 if prem_a[c] == prem_b[c] else 0.0)
        else:
            pa = 1 / (1 + np.exp(beta * (np.log(prem_a[c]) - np.log(prem_b[c]))))
        for side, p, pr in (("A", pa, prem_a[c]), ("B", 1 - pa, prem_b[c])):
            keep = 1 - lapse if losses[c].mean() < 0.5 * pr else 1.0
            if p * keep > 0:
                w[side][c] = p * keep
    res = {}
    for side, pr in (("A", prem_a), ("B", prem_b)):
        P = sum(pr[c] * x for c, x in w[side].items()); L = sum(losses[c].mean() * x for c, x in w[side].items())
        res[side] = {"won_weight": sum(w[side].values()), "won_LR": (L / P) if P else None,
                     "won_CR": (L / P + EXPENSE) if P else None, "won": sorted(w[side])}
    return res


def not_tested_gap(prem, losses, clean, outside="F0", tested="F2"):
    """E4: per-configuration P(outside) - P(tested), $ and % of P(outside), split by risk group."""
    med = float(np.median([losses[c].mean() for c in losses]))
    rows = {c: {"usd": prem[outside][c] - prem[tested][c],
                "pct_of_outside": (prem[outside][c] - prem[tested][c]) / prem[outside][c],
                "group": "clean" if c in clean else ("low" if losses[c].mean() < med else "high")} for c in prem[tested]}
    agg = {g: float(np.median([r["pct_of_outside"] for r in rows.values() if r["group"] == g]))
           for g in ("clean", "low", "high") if any(r["group"] == g for r in rows.values())}
    return rows, agg


def rescale_factor(losses, f):
    """E6: common factor k so the book-mean realised loss equals f x mean event severity (events = conversations
    with positive loss; their mean loss is used as E[severity])."""
    allx = np.concatenate(list(losses.values()))
    sev = float(allx[allx > 0].mean()) if (allx > 0).any() else 0.0
    return f * sev / float(allx.mean()) if allx.mean() > 0 else 0.0


def buyer(prem_per_conv, el_per_conv, saving=SAVING):
    """E5 (real-world assumption): premium / (saving x resolution rate) and premium / expected loss."""
    return {"premium_over_saving": prem_per_conv / (saving * RESOLUTION),
            "premium_over_EL": prem_per_conv / el_per_conv if el_per_conv > 0 else None}


def kill_criteria(books_ii, mkt_f0_f2, books_ii_corr_roc):
    ke1 = not any(b["CR"] <= CR_TARGET for b in books_ii.values())
    a, b = mkt_f0_f2["A"]["won_LR"], mkt_f0_f2["B"]["won_LR"]          # A = F0, B = F2
    ke2 = (a is None or b is None) or (a - b) < 0.10
    ke3 = all(r < COST_EQUITY for r in books_ii_corr_roc.values())
    return {"KE1": bool(ke1), "KE2": bool(ke2), "KE3": bool(ke3)}


def run_all(forecasts, losses, cards, base_model, clean, seed=0):
    rng = np.random.default_rng(seed)
    fc, mods = add_outside_in(forecasts, cards)
    boots = boot_means(losses, rng)
    out = {"card_modifiers": mods, "books": {}, "markets": {}, "gap": {}, "kill": None}
    prem = {}
    for rule in ("i", "ii"):
        for plr in PLR_SWEEP:
            for v in V_SWEEP:
                for f in fc:
                    p = premiums(fc[f], rule, plr)
                    if plr == PLR:
                        prem[(rule, f)] = p
                    out["books"][f"{f}|{rule}|PLR{plr}|V{v}"] = book(p, losses, boots, base_model, clean, v)
    P2 = {f: prem[("ii", f)] for f in fc}
    for other in ("F0", "F0q", "F1_3", "F3"):
        if other not in P2 or "F2" not in P2:
            continue
        for beta in (None, BETA):
            for s in LAPSE:
                out["markets"][f"{other}_vs_F2|beta{beta}|lapse{s}"] = market(P2[other], P2["F2"], losses, rng, beta, s)
    for o in ("F0", "F0q"):
        for rule in ("i", "ii"):
            out["gap"][f"{o}-F2|{rule}"] = not_tested_gap({k: prem[(rule, k)] for k in (o, "F2")}, losses, clean, o)[1]
    base = {f: out["books"][f"{f}|ii|PLR{PLR}|V{V}"] for f in fc}
    out["kill"] = kill_criteria(base, out["markets"]["F0_vs_F2|betaNone|lapse0.0"], {f: b["RoC"] for f, b in base.items()})
    out["rescale"] = {str(f): rescale_factor(losses, f) for f in FREQ_SWEEP}
    return out
