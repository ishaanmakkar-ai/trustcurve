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

### Post-hoc deviations in the phase-0 run above (labelled per review 4 #9)
None of these were in the pre-registration:
- 150 reps were run, not 200.
- The capped pure-premium estimand was added after the uncapped one failed.
- Log-scale intervals were chosen after Wald under-coverage was seen.
- The "≥2,000 runs" qualifiers on T2 and capped PP were added after seeing results.
- T1's max bias of −5.3% slightly exceeds the pre-registered < 5%.
- The ICC grid values are **latent-scale**, which the pre-registration didn't state.

## Phase 0 v2: re-run after review 4 (pre-registered 2026-10-21, before code changes)
**Changes to the simulator and design (all decided before seeing new results):**
1. **Fixed stratified allocation:** parents per stratum = round(n_par × mix), with a minimum of 2 per stratum. No empty strata. The variance uses the same clustered linearisation.
2. **Sampling arms:**
   - **PROP:** sample at the assumed real mix W.
   - **NEYMAN:** allocation ∝ W_h·σ_h, where σ_h is the per-parent outcome SD. An oracle version gives the upper bound; a plug-in version uses σ_h from a 300-run pilot sample.
   - **IS_MIX:** kept for comparison.
3. **Realistic control variate (T4r):** a **pre-run, task-level** score s_p = sigmoid(c + r·z_p + √(1−r²)·ε), where z_p is the standardised parent logit, r ∈ {0.3, 0.6} and the calibration offset c ≠ 0.
   - The pool mean is **estimated** from an independent sample of 1,000 pool tasks (their scores only; no runs needed), and its variance is added to the SE.
   - β is **cross-fitted**: estimated on one half of the parents and applied to the other.
4. **Credibility where it bites (T2f):** 30 fine workflows with 2–8 parents each and 2 runs per parent.
   - The target is each workflow's rate.
   - Raw per-workflow means are compared with the Bühlmann–Straub estimate (parents as the units within a workflow, workflows as classes, complement = pooled mean), using per-workflow MSE and the coverage of an empirical-Bayes interval.
5. **Near-miss (T3p):** counts ~ Poisson(R·p), R = 10, so there's no saturation. Three ways of getting R:
   - (i) R known;
   - (ii) R estimated from an **independent calibration sample** of 2,000 runs on another stratum mix, with its uncertainty propagated;
   - (iii) R misspecified × 1.5.
6. **Grid:**
   - q ∈ {0.5%, 1%, 2%, 5%}, with q = 0.5% and 1% as the zero/low-event arm
   - **latent** ICC ∈ {0.1, 0.3, 0.6, 0.8, 0.9}; observed-scale ICCs are reported alongside
   - parent share ∈ {0.5, 0.9}
   - runs ∈ {500, 2,000, 8,000}
   - **300 reps** per cell
7. **Zero-event interval:** when the estimate is 0, the upper bound is the Clopper–Pearson one-sided 95% bound on n_eff = parents (the worst case over heterogeneity); the lower bound is 0.
8. **Mix misspecification arm:** the truth uses W_true (5 points moved from cancel to refusal); the estimators use the assumed W.
9. **Metrics:**
   - relative bias
   - two-sided 90% coverage
   - **one-sided 95% upper-bound coverage** (truth ≤ upper)
   - relative half-width
   - pooled coverage across cells with Monte Carlo SE
   - worst cell
   - **runs and distinct parents** needed for ±20%, for designs with 1, 2 and 10 runs per parent

**Predictions:**
- **P1:** PROP and NEYMAN need fewer runs than IS_MIX for the *mixed* rate (ratio 0.7–0.9). IS only helps for **stratum-level** estimates of rare strata.
- **P2:** the realistic T4r cuts the half-width by ≤ 10% at r = 0.3 and 10–25% at r = 0.6. At r = 0.3 it may not beat simply adding runs.
- **P3:** T2f beats raw per-workflow means on MSE by ≥ 20% when workflows have few parents, with empirical-Bayes interval coverage of 0.85–0.95. T2 on 5 coarse strata ≈ post-stratification (rebutted as "untested", not "failed").
- **P4:** T3p is unbiased with R known; with R from a calibration sample it's unbiased only if R is the same across strata. Under ×1.5 misspecification the bias is −33%.
- **P5:** at q ≤ 1% with 500 runs, two-sided coverage drops below 0.85. The CP-on-parents upper bound keeps one-sided coverage ≥ 0.95.
- **P6:** the mix-misspecification arm biases every estimator by roughly the size of the mix error (+10–20%). **No technique fixes a wrong W.**
- **P7:** at latent ICC 0.8–0.9 (pilot-like), ±20% needs ≥ 10,000 runs, and **parents, not runs, bind**: at 1 run per parent the parent count is about 4,000.

**Pass rule (unchanged):**
- |bias| ≤ 10%
- pooled coverage within 0.85–0.95, with Monte Carlo SE reported
- plus the new criterion: **upper-bound coverage ≥ 0.93**

## E1: user-simulator A/B (H-setup), pre-registered 2026-10-21, before any E1 run
**Design:**
- The same 25 breadth tasks (`results/pilot/breadth_tasks.txt`), 2 runs each, agent = `claude-haiku-5-5`, judge = Haiku.
- Arms (user simulator):
  - **H** = `claude-haiku-5-5` (the existing pilot breadth runs, 50)
  - **O** = `openai/gpt-6.1-sol` (Hexa Agents credits)
  - **S** = `claude-sonnet-5-5`
- O and S both cost $2/$10 per MTok, so price is matched: O vs S isolates model **family**, and {O, S} vs H isolates **strength**.

**Outcomes:**
- failure (reward < 1)
- DB mismatch
- omission
- insured loss event
- attribution of each failure (RUBRICS A)

**Analysis:**
- Per-task paired difference in failure rate (arm − H), with a task-level bootstrap 90% CI.
- McNemar-style exact test on task-level majority outcomes.
- Minimum detectable effect at 80% power, given 25 paired tasks and the observed discordance.

**Hypotheses:**
- **H1:** failure rate S < H and O < H, driven by fewer **user_caused** failures. Expected direction: −5 to −15 points. Not significant is likely at n = 25 (MDE ≈ 20 points).
- **H2:** the set of failing tasks differs between arms. Expect ≥ 3 tasks to flip, with the observed task-level ICC reported per arm.
- **H3:** the insured-loss rate stays ≈ 0 in every arm (commission is agent-driven).
- **H4 (family):** O and S don't differ by more than the MDE.

**Kill criterion:** if user_caused accounts for ≥ 30% of H's failures and drops to < 10% under S or O, the pilot's failure rates are **setup-inflated**, and every downstream estimate must use the stronger simulator.

**Spend estimate:** about $1.3 for O (Hexa) and about $2.8 for S (personal).
