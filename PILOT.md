# Pilot results (2026-10-21)

**Question:** how many runs before you can insure an AI agent? We tested this on τ²-bench airline (tau2 v2.0.0) with Claude Haiku 5.5 as the agent, the user simulator and the judge.

## Headline
1. **0 insured loss events in 65 runs** (27 distinct tasks).
   - Every failure was an **omission**: a missed sale, a refund not processed, a change not made, or a hand-off to a human.
   - One run diverged from gold with a $4,418 refund. That refund was **customer-requested and policy-permitted** (a business-class cancellation), so it is not a wrongful payout.
   - With clustering, the 95% upper bound on this agent's insured-loss rate is **about 8% per conversation**.
2. **Failures cluster hard by task** (ICC 0.59). 65 runs are worth only **about 36 effective runs**.
3. **You cannot reach any credibility standard on τ²-bench airline by repetition.**
   - With 50 tasks and ρ ≈ 0.6, the ceiling is **about 85 effective runs**, however many repeats you do.
   - Even the loosest standard (±20% at 90%) on a *stressed* 20% loss rate needs about **480 distinct tasks**.
   - A realistic 2–5% loss rate needs **2,000–40,000+ distinct tasks**.
   - Compute is cheap (**$0.015 and 37 s per run**). The bottleneck is **distinct tasks**.
4. A benchmark score is not an insurance input. Pass^1 here was 0.82 on the breadth batch, but **benchmark failure ≠ insured loss**. Our loss accounting changed twice when we read transcripts (ITERATIONS.md loops 2–3).

## Numbers
| | Pilot batch (5 tasks × 3) | Breadth batch (25 random × 2) | Combined |
|---|---|---|---|
| Runs | 15 | 50 | 65 |
| Benchmark pass^1 | 0.60 | 0.82 | — |
| DB mismatch | 4 | 8 | 12 |
| Omission runs ($ recorded, not insured) | 6 | 7 | 11 (some failures are COMMUNICATE-only) |
| Raw commission divergences | 0 | 1 ($4,418, policy-permitted) | 1 |
| **Insured loss events** | 0 | 0 | **0** |
| Cost | $0.243 | $0.735 | **$0.98** (+$0.02 smoke) |

- Failure ICC: 0.59. Effective runs: 35.6. One-sided 95% upper bound on the loss rate: 8.1%. Wilson 95% on the breadth loss-event rate before the policy check: 0.4–10.5%.
- Token cost matched tau2's per-message cost on every run. Haiku 5.5 is priced at $0.10/$0.50 per MTok. The communicate-judge cost is not in these totals (it has small, separate usage).

## Projection for the main run (`results/pilot/projection.json`)
In effective runs, binomial limited-fluctuation standard with 1,082·(1−q+CV²)/q runs, and ρ = 0.59 (failure ICC as a proxy, since the loss ICC can't be estimated with 0 events):

| Option | Runs | Cost | Time (8 parallel) | What it buys |
|---|---|---|---|---|
| **A** all 50 tasks × 20 | 1,000 | $15 | 1.3 h | About 82 effective runs. Tightens the loss-rate *upper bound* to about 3.5% if still 0 events. Can't price a premium credibly |
| **B** ±20% on frequency, stressed q = 20%, CV² = 1 | 968 runs over 484 tasks | $15 | 1.3 h | Needs **484 distinct tasks** (τ² has 50) |
| **B′** ±10%, q = 5%, CV² = 1 | 16,762 runs over 8,381 tasks | $252 | 22 h | Needs 8,381 distinct tasks |
| **C** full standard (±5%), q = 2%, CV² = 3 | 342,108 runs over 171,054 tasks | $5,148 | 442 h | Infeasible as a benchmark exercise |

**Recommendation:** don't buy option A as "the main run". 1,000 repeats of 50 tasks is mostly wasted, because the clustering ceiling binds. Instead:
1. **Generate distinct task variants.** Perturb τ² airline tasks: customers, reservations, policy edge cases, adversarial requests. Validate each variant's gold with a solver.
2. **Stress the commission peril.** Add tasks where the correct action is *refusal* (non-refundable cancellations, compensation requests that aren't owed, social-engineering prompts), because that's where wrongful payouts live.
3. **Price with credibility blending.** Combine a thin observed rate with a scenario-based manual rate. Report the premium with its uncertainty buffer, rather than claiming full credibility.
4. **Fix the user simulator.** Use a stronger, different model (e.g. Sonnet 5.5) held constant. At least one pilot failure (task 14) was caused by the simulator, not the agent.

A cheap next step (about $1.50): **all 50 tasks × 2** to finish breadth, plus a first set of 20–30 refusal and adversarial variants.

## Errors found and fixed (details in ITERATIONS.md and REVIEW.md)
- **Loop 1:** the integration tests were vacuous (tasks 0–4 move no money) and the replay outputs were blank. Fixed, with non-vacuity guards.
- **Loop 2:** the netted dollar diff scored **missed bookings as payouts**. Rebuilt it to classify by transaction (payout / harm / omission). Review 1 also found **gift-card downgrade refunds double-counted** ($10,488 vs the true $5,244); fixed and regression-tested.
- **Loop 3:** a divergence from gold isn't a wrongful act. Added a **policy-compliance layer** (tau2 cancellation rules) that separates wrongful from permitted payouts.
- **Review 1 (15 points):** a unit error in the credibility ceiling (effective runs vs claims), a too-small pilot design, strata defined from gold, the same model used for user and judge, the seed dropped by LiteLLM, weak tests and a z-value typo. All resolved or documented.

## Open problems
- **The loss ICC is unestimated** (0 events). The failure ICC is used as a proxy and may differ.
- **Severity CV is unknown** with no insured events. Scenarios use CV² of 1–3.
- **The insurance-reason cancellations** (policy rule 4) are "uncertain"; none occurred in the pilot.
- **Compensation and overcharge legitimacy** (beyond cancellations) isn't policy-checked yet.
- **The communicate-judge cost** isn't counted.
- **The exposure unit** (one conversation) and the real-world workflow mix are assumptions.
- **Results apply only to this rating cell:** Haiku 5.5 agent, Haiku user simulator, tau2 v2.0.0 airline.

## Next step
Build a task-variant generator with solver-validated gold, plus a refusal/adversarial task set. Run all 50 tasks + variants × 2 with a Sonnet 5.5 user simulator. Then fit the frequency/severity, credibility blend and premium with its uncertainty buffer (full goal M2–M3).
