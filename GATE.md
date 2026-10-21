# GATE report — Goal 3 v2, after phase 0, phase 1 and phase 1b (2026-10-21)

**Status:** phase 0, phase 1 (E1, E1x, E2, E3, labels, reference run) and phase 1b are complete, pre-registered in EXPERIMENTS.md, reviewed (REVIEW.md reviews 4–6) and pushed. **Phase 2 has not started. It needs an explicit go.**

**Spend:** ≈ $81 of the $300 cap (pilot ≈ $1; phase 1 ≈ $80: runs $79.44, labels $0.77; the reference run was $36). Remaining ≈ $219.

## Recommendation: NO-GO on phase 2 as specified; GO on a staged validation path instead (≈ $10 to validate, then ≈ $90 to scale only if validation passes)

Phase 2 as written assumed **variants of benchmark tasks can stand in for new tasks**, and that **the loss metric measures loss**. Phase 1 refuted both:
1. Five variants of a task are worth about **1.6–1.8 independent tasks**, not 5 (E2).
2. The dollar-diff behind "insured loss" **overstated money harm about 100×** on the 1,000-run reference set (transcript audit).

Spending ≈ $120 on a 7,600-run credibility run now would produce a precise-looking number on the wrong unit, measured with a broken ruler.

**Strongest case against this recommendation:** the budget is there, and the infrastructure works. A 7,600-run run on τ² variants would produce a headline "N effective failures" figure for Fulcrum, and DB mismatch (the sizing proxy) isn't affected by the dollar-diff bugs. The counter-argument: with ρ_parent ≈ 0.43 and 50 parents, the effective sample tops out at about 100–120 runs (≈ 18–22 effective failures) however many variants are run. So the headline would be false precision.

## The four questions the gate asks

### 1. Do variants count as near-independent tasks? **No.**
- ρ_parent (DB mismatch) = 0.43 [0.23, 0.63].
- Cross-variant correlation r_cross = 0.73 [0.46, 0.96].
- V_eff on the observed scale: **1.58 of 5 at 2 runs per variant (90% CI 1.27–2.22)** and 1.84 at 1 run (1.42–2.63). P(V_eff ≥ 3) ≤ 0.006.
- The pre-registered rule (≥ 3 = viable) fails. Phase 2 would need **new task families**, not variants.

### 2. Which techniques passed?

| Technique | Phase 0 (known-truth simulator) | Phase 1 (real runs) | Verdict |
|---|---|---|---|
| Sample at the real workflow mix (PROP), task-clustered log interval | ✓ cov 0.90 | ✓ at a ~19% rate (cov 0.96; 0.885 with FPC). ✗ at 0.9% harm: 0.83 among non-zero slices | **Use for common outcomes**; rare-event intervals unvalidated |
| Zero-event CP-on-tasks fallback | ✓ | used in E3 (0/120 → ≤ 7.2% per task) | **Use** |
| Credibility (Bühlmann–Straub) point estimates per workflow | ✓ MSE −69 to −91% | ~ MSE −30%, but **the grand mean does better** (VHM floored; workflows indistinguishable at this design) | Use only where between-workflow variance is detectable |
| Capped pure premium | ✓ | not yet meaningful (severity metric broken) | Pending dollar-diff v4 |
| Importance sampling for the overall rate | ✗ needs 1.2× the runs | — | Rare-workflow estimates only |
| Neyman allocation (plug-in) | no gain | — | Drop |
| Control variate (pre-run score) | ✗ no gain at realistic r | — | Drop |
| Near-miss counts | only with an externally known ratio | 1 near-miss in 160 refusal runs | Drop unless R is known |
| Variants as extra tasks | — | ✗ V_eff ≈ 1.6–1.8 of 5 | Drop |
| Template-generated refusal tasks | — | ✗ 160/160 passed (no risk signal) | Needs a fidelity pilot |
| Haiku LLM labeller for attribution | — | moderate: κ = 0.45 vs a blinded second rater | Use with a human audit |
| Dollar-diff v3 + policy layer (severity) | — | ✗ flagged $14,071 vs $145 genuine; 4 systematic bugs | **Fix (v4) before any loss estimate** |

### 3. Effective failures reachable under the remaining ≈ $219
A Haiku-agent/Haiku-customer run costs **$0.016** (REF-H: $16.08 / 1,000).

| Route | Ceiling | Effective failures (DB mismatch, q ≈ 0.19) | Effective money-harm events (q ≈ 0.9%) |
|---|---|---|---|
| τ² airline only (50 tasks, ρ ≈ 0.52) | about 50/ρ ≈ **96 effective runs**, whatever the spend | ≈ 18 | ≈ 1 |
| τ² variants (any number per parent) | about 50/ρ_parent(0.43) ≈ **116 effective runs** | ≈ 22 | ≈ 1 |
| New generated tasks, 1 run each | budget ≈ 13,600 runs, **if** a generator yields that many valid, realistic tasks | up to ≈ 2,500 | ≈ 120 |

- **The 1,082-effective-failure target is out of reach on τ² airline, with or without variants.**
- It is reachable in DB-mismatch terms **only with thousands of new, realistic tasks**, and E3 shows the current template generator doesn't produce realistic risk.
- For **money harm** (≈ 0.9% of runs among flagged runs, $9–$30 each, on only 3 of 50 tasks), ±20% precision needs about **7,500 distinct tasks** if harm were spread evenly. Because it clusters on "trap" tasks, precision depends on how many such tasks a generator produces: at about 1% and 1 run per task, 3,000 tasks give ±32% and ±16% needs about 10,000 (review 6).

### 4. Go / no-go
**No-go** on phase 2 as specified. **Proposed instead (needs your go; steps 1–3 ≈ $10, step 4 ≈ $90; about 2 days):**
1. **Dollar-diff v4** ($0). Fix the 4 audited bugs:
   - $0 changes counted as charges
   - cross-reservation netting
   - header fields in the pairing key
   - consent and permission checks

   Pass condition: it reproduces the audit's classification on all 33 REF-H flags plus E2's 2 (genuine $145 ± rounding), **and** a random audit of about 50 unflagged mismatch runs finds no missed harm. Severity is also extended to consequential loss (wrong-date travel, forced extra cash).
2. **Human attribution audit** (your time, ≈ 1 hour): 30 failed transcripts, to calibrate the labeller (κ 0.45 today).
3. **Generator fidelity pilot** (≈ $6–8 including generation; review 6 suggests scaling this to about 300 tasks, ≈ $15–20, once v4 exists): 50 new LLM-generated airline tasks (not templates), validated against policy, × 2 runs, under the Haiku and Sonnet customers.
   - Pass: failure rate 10–35% and DB-mismatch ICC 0.3–0.7, i.e. benchmark-like.
   - Kill: failure < 5% (the E3 ceiling again) or > 50%, or validation yield < 50%.
4. **Only if 1–3 pass:** about 1,300 distinct generated tasks × 1 run with two simulators: Haiku customer ≈ $21, Sonnet customer ≈ $52, plus generation (≈ $90 total). At q ≈ 0.19, ±20% on DB-mismatch frequency needs only about 300 tasks per simulator, so 1,300 also supports per-workflow estimates. Money harm at about 1% gives about 13 events, a first frequency of roughly ±45%. **That isn't credible for pricing**, so a priced premium would still rest mostly on the complement. Pricing would use PROP + capped pure premium, with credibility only where workflows separate.

**Kill criteria for the whole approach:**
- v4 can't match a human reading of the 35 audited cases.
- Or generated tasks keep failing the fidelity pilot after one revision.
- Or the two simulators disagree on agent ranking at 1,300 tasks.

Any one of these means "benchmark-derived loss frequency isn't viable yet", which is itself a publishable negative result.

## Headline findings (with their caveats)
1. **Simulator choice moves measured risk by about 10 points.** A Sonnet customer lowers the Haiku agent's failure by 10.6 points [5.4, 16.2] (exact p = 0.002, 25 tasks × 20 runs), concentrated in 10 of 25 tasks. Which simulator is more realistic is unknown. Simulator choice is a first-order pricing assumption.
2. **The simulator changes the agent gap; a full reversal isn't established.**
   - Sonnet beats Haiku under the Haiku and Sonnet customers, but loses under the OpenAI customer: +8 points DB mismatch [+2, +16].
   - The interaction is the robust part (6/0 tasks, p = 0.03). Δ_O itself rests on 3 tasks (p = 0.25).
   - Neither pre-registered kill rule fires as written. A post-hoc baseline swap meets the hard rule's condition arithmetically, but only through a sparse-bootstrap artefact (review 6 #4).
   - Both agents are Claude models, so this is not evidence of same-family bias.
3. **Wrongful payouts by the agent are ~0 among audited runs** (all flagged runs plus all 8 unflagged over-refunds; about 147 other mismatch runs are unaudited), across 1,985 Haiku-agent runs and 190 Sonnet-agent runs. The only REF-S flag (task 35, $163) follows the pattern the audit netted to −$127 on REF-H, but wasn't itself audited. **Customer-overcharge harm is about 1% of runs, at $9–$30.** On these tasks the commission peril is small and frequent-ish, not rare and large.
4. **55% of audited failures are task-ambiguous.** Gold answers on τ² airline tasks 7, 32 and 44 conflict with their own instructions, so raw failure rate is a noisy risk proxy. DB mismatch is less affected.
5. **Clustering is high:** ICC 0.52. One task is worth about 2 runs, so distinct tasks, not repeats, are what buy precision.

## Open items carried forward
- Human attribution audit (review 5 #4).
- Dollar-diff v4 and permission-checking change refunds (review 5 #3, audit).
- A non-Claude agent, to test same-family simulator bias (the deferred 3 × 3).
- Whether DB mismatch is a valid proxy for insured loss: unvalidated, and given finding 3, probably weak.
