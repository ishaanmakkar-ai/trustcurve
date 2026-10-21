# Pilot plan

**Question the pilot answers:** what does it cost, and is it even possible, to price one AI-agent configuration on τ²-bench airline with insurance-grade credibility? What must the main run look like?

## Rating cell (the unit)
One configuration:
- agent `anthropic/claude-haiku-5-5`
- user simulator `anthropic/claude-haiku-5-5`
- communicate judge `anthropic/claude-haiku-5-5`
- tau2 v2.0.0 (commit recorded), `llm_agent`, airline policy, provider-default sampling

Haiku 5.5 rejects non-default temperature, and the default is also what a deployment would run. Haiku 5.5 runs with adaptive thinking on at effort `medium`, its provider defaults. The seed is dropped by LiteLLM for Anthropic, so it's a label only; reproducibility comes from the saved transcripts. **Nothing is pooled across configurations.**

## Exposure unit
One run (one customer conversation). This is valid only if real traffic has a similar per-conversation loss profile. The workflow mix will be reweighted with labelled assumptions.

## What we measure per run, and why
| Measure | Why insurers need it |
|---|---|
| `task_id`, `trial`, `seed` | Clustering: the ICC drives the effective sample size |
| pass/fail (tau2 reward) plus the DB and COMMUNICATE components | Benchmark failure ≠ insured loss; keep both |
| **loss event** = money mismatch vs gold | The frequency that's actually priced |
| signed $ delta, first-party loss, third-party harm, severity | Severity distribution and CV² drive the required n |
| non-monetary DB mismatch flag | Wrong flights or seats with $0: a separate peril, not $0 risk |
| tokens (input/output per role), $ cost from tokens × official price | Sizing the main run |
| wall-clock duration, termination reason | Throughput and failure modes (timeouts, errors) |
| stratum: the task's money-moving action types | Reweighting to a workflow mix |

Prices: Haiku 5.5 is $0.10 / $0.50 per million input/output tokens for prompts ≤100K (official Anthropic price table, cached 2026-10-06). Smoke test: about $0.019 and 48 s per run, excluding the judge.

## Design
- **Tasks:** 5 airline tasks, chosen to include **at least 3 money-moving tasks** so a loss is possible, plus at least 1 non-money task as a control.
- **Repeats:** 3 runs each, 15 in total. Base seed 20261021.
- **Expectations, written before running:**
  1. Every run completes with no infrastructure errors, at $0.01–0.05 per run.
  2. For runs whose DB matches gold, the dollar diff reports zero loss. If any matching run shows a loss, the dollar diff is wrong.
  3. At least one failure across 15 runs. The Haiku-class failure rate on airline is likely 30–60% `[U]`.
  4. Failures cluster by task, so the ICC is positive.
  5. COMMUNICATE-only failures carry $0 loss.

## Checks that could fail (iteration triggers)
- The DB-match flag and money match disagree in the impossible direction (DB match but nonzero $).
- The token cost doesn't reconcile with tau2's per-message cost.
- Fewer than 3 failed transcripts to read, or a failure caused by the user simulator rather than the agent (read ≥3).
- Seeds or trials that aren't actually independent (identical transcripts across trials).

## Projection rules (step 7)
- Use q (loss-event rate), CV_X² and ρ (ICC) from the pilot. With 15 runs these will be noisy, so report ranges.
- Runs needed = (z/k)²·[(1−q) + CV_X²]/q × DEFF. Check this against the **ceiling N_tasks/ρ**: with 50 tasks, the effective n is capped at roughly 50/ρ.
- Give three options:
  - **A.** all 50 tasks × 20 runs, the affordable fallback
  - **B.** what it takes to reach k = ±10% or ±20% on frequency
  - **C.** what reaching the full standard needs, stated in effective runs (1,082·(1−q+CV²)/q vs the N/ρ ceiling, with ρ of the loss-event indicator). This likely means more distinct tasks, not repeats

**Correction after review 1:** batch 1 (5×3) is plumbing and cost only. Estimates of q, ρ and CV² come from loop 3 (a random 25 tasks × 2, with a task-level bootstrap). Strata are the customer's request type, not gold actions. Loss = payout_loss + customer_harm; omissions are reported separately.

## Commercial framing
- **Who uses this output:** an MGA or Lloyd's syndicate deciding whether to write agent liability cover for a customer-service deployment, at what limit and deductible.
- **Decision it changes:** "with N distinct tasks you can quote within ±X%; below that, price it as a manual rate plus a risk load".
- **Why it matters for Ishaan:** it's the evidence layer an AI-agent insurer needs. EF and BlueDot reward exactly this kind of concrete, falsifiable work.
