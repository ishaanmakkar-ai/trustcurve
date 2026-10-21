# Experiments (Goal 3 v2): pre-registered hypotheses

Each block below was written **before** the corresponding code or run. Results are appended under each block, never edited into it.

## Phase 0: offline validation of techniques on a known-truth simulator (pre-registered 2026-10-21)

**Simulator** (`src/trustcurve/simstudy.py`):
- **Parent tasks:** latent logit loss propensity θ_p ~ N(μ_h, σ_P²) within stratum h (cancel, change, book, compensation, refusal).
- **Variants:** θ_pv = θ_p + N(0, σ_V²).
- **Runs:** Bernoulli(sigmoid(θ_pv)).
- **Clustering:** σ_P and σ_V are set to hit a target total ICC of 0.1, 0.3 or 0.6, with a parent share of 50% or 90%.
- **Severity:** lognormal (σ = 1.2), with stratum-specific scale.
- **Near-misses:** Bernoulli(min(1, R·p)), with R = 10.
- **Risk score:** sigmoid(θ_pv) + N(0, 0.05²).
- **Truth:** the loss rate and pure premium under an **assumed real-world mix** w: cancel 0.35, change 0.35, book 0.20, compensation 0.05, refusal 0.05.
- **Benchmark sampling mix:** deliberately different. Cancel-heavy, with refusal oversampled for importance sampling.

**Techniques**, each with a nominal 90% interval from **parent-level** cluster-robust SEs unless stated:
- **T0 naive:** unweighted mean of a benchmark-mix sample. *Expected: biased* whenever the strata differ, with coverage well under 90%.
- **T1 importance sampling:** oversample high-risk strata, then self-normalise reweighting by w_h/s_h. *Expected: unbiased (|relative bias| < 5%), coverage ≈ 90% (85–95%)*, and a narrower interval than T0-reweighted at the same budget when risk is concentrated in the oversampled strata.
- **T1-var:** T1 with errors clustered at the **variant** level instead of the parent. *Expected: under-covers*, worse as the parent share rises. This is the gate's mechanism.
- **T2 Bühlmann–Straub per stratum**, credibility-weighted to the pooled mean, then mix-weighted. *Expected:* small shrinkage bias (< 10% relative), coverage ≈ 90% via cluster bootstrap, and the narrowest interval when there are many strata with few tasks.
- **T3 near-miss ratio:** p̂ = near-miss rate / R. *Expected: unbiased with R correct.* With R misspecified by ±50%, bias of −33% or +100%, so it is **only usable with an externally validated R**.
- **T4 control variate:** risk score X with a known pool mean. *Expected:* unbiased, with variance cut by about (1 − corr²).

**Pass rule:** |relative bias| ≤ 10%, coverage between 85% and 95%, and runs-to-±20% reported. A technique that fails is dropped from phase 1.

**Grid:**
- true mixed loss rate ≈ 2% or 5%
- total ICC 0.1, 0.3 or 0.6
- parent share 0.5 or 0.9
- run budgets of 500, 2,000 and 8,000
- 200 Monte Carlo replications per cell

The simulator's assumptions (logit-normal heterogeneity, a fixed ratio R, lognormal severity) are themselves untested on real data. Phase 1 checks them.

### Phase 0 results (2026-10-21)
Files: `results/phase0/grid_final.json`, `results/phase0/summary.json`. 36 cells × 150 replications. Log-scale intervals after loop 2; earlier grids are kept for the record.

| Technique | Median abs. bias | Max bias | Coverage (median; at 500 / 2,000 / 8,000 runs) | Half-width vs T1 | Pre-registered prediction | Verdict |
|---|---|---|---|---|---|---|
| T0 naive (benchmark mix) | 15.0% | −19.7% | 0.74 (0.84 / 0.76 / 0.41) | — | biased | ✓ predicted, **fail** |
| T0w benchmark reweighted | 1.1% | −8.1% | 0.88 | 1.31 | — | ok, but needs **~1.7× the runs** of IS |
| **T1 importance sampling** | 1.0% | −5.3% | 0.89 (0.85 / 0.89 / 0.90) | 1.00 | unbiased, ≈ 90% | ✓ **pass** |
| T1-var (variant clusters) | 1.0% | −5.3% | 0.84 (0.83 / 0.85 / 0.86) | — | under-covers | ✓ predicted |
| T1 pure premium (uncapped) | 1.4% | −9.9% | 0.83 (0.78 / 0.85 / 0.85) | — | — | **fail** (heavy tail) |
| **T1 pure premium, capped at $2,000** | 0.9% | −8.3% | 0.87 (0.82 / 0.89 / 0.89) | — | — | ✓ **pass** at ≥2,000 runs |
| **T2 Bühlmann–Straub** | 0.9% | −5.8% | 0.87 (0.81 / 0.88 / 0.89) | 0.94 | small bias, ≈ 90% | ✓ **pass** at ≥2,000 runs |
| T3 near-miss, R correct | 21.3% | −48.6% | 0.09 | — | unbiased if R correct | ✗ **prediction wrong** (saturation), **drop** |
| T3 near-miss, R × 1.5 | 47.5% | −65.7% | 0.00 | — | biased | ✓ predicted, **drop** |
| **T4 control variate** | 0.9% | −9.8% | 0.88 (0.87 / 0.89 / 0.91) | 0.86 | unbiased, narrower | ✓ **pass** (needs a known score mean) |

**Runs for ±20% at 90% with T1** (simulated; 5 variants × 2 runs per parent):

| Target | q = 2%, ICC 0.1 / 0.3 / 0.6 | q = 5%, ICC 0.1 / 0.3 / 0.6 |
|---|---|---|
| Loss rate | 4,473 / 5,286 / 8,724 | 1,981 / 2,609 / 4,476 |
| Capped pure premium | 7,620 / 8,725 / 12,458 | 3,467 / 4,132 / 6,084 |

**Implication for H-main:**
- In simulation, ±20% is reachable with about 2,000–12,500 runs, roughly $30–185 on a Haiku simulator, **provided** there are about 200–1,250 genuinely independent parent tasks.
- Phase 1 tests whether real variants and refusal tasks behave like the simulator assumes. In particular, E2 measures ρ_parent.
