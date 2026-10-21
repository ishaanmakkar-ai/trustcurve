# Independent review log

Reviewers are fresh-context agents that see only the repo files. Each point is resolved or rebutted here.

## Review 1 — after step 2 (research, plan, dollar diff v1), 2026-10-21
| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | A gift-card downgrade both restores the balance and appends a negative entry, so the balance-based position counted the refund twice (task 11: $10,488 vs $5,244) | **Fixed.** v2 classifies by transaction entries, not balances. Regression test: task 11 = exactly $5,244, recorded once. `position_delta_legacy` is kept only as a labelled cross-check and is known to double-count gift-card downgrades |
| 2 | Blocker | Missed bookings and missed cancellations scored as payout or harm | **Fixed** (found independently in loop 2). Omissions are a separate category, excluded from base severity |
| 3 | Major | The N/ρ ceiling counts effective *runs*; effective *claims* ≈ q·N/ρ, so "1,082 effective failures" is mis-unit | **Accepted.** RESEARCH and PILOT_PLAN corrected: every target is in effective runs, compared as 1,082·(1−q+CV²)/q against N/ρ. ρ must be the ICC of the *loss-event* indicator |
| 4 | Major | 5×3 can't estimate q, ρ or CV², and the hand-picked tasks bias q | **Accepted.** Batch 1 is labelled plumbing and cost only. Loop 3 adds random 25 tasks × 2. Intervals come from a task-level bootstrap |
| 5 | Major | Strata and "control" were defined from gold actions; the insurable peril lives on tasks whose correct answer is refusal | **Accepted.** Strata are now the customer's request type; refusal and no-action tasks are included in the random batch |
| 6 | Major | The same model plays agent, user simulator and judge, so user errors get charged to the agent | **Partly accepted.** Kept for the pilot (Anthropic-only, cheap). Every failed transcript is classified as agent- or user-caused, and q is reported with user-caused failures removed. Recommendation for the main run: a stronger fixed user simulator (e.g. Sonnet 5.5), held constant |
| 7 | Major | Coverages were summed into one severity | **Accepted.** payout_loss (first-party) and customer_harm (third-party) are reported separately. Harm is at face amount, labelled as an upper bound on remediation cost |
| 8 | Major | The seed is dropped by LiteLLM for Anthropic, so it's a label only | **Accepted.** Documented. Reproducibility comes from saved transcripts plus a dollar-diff re-run |
| 9 | Major | Vacuous or weak tests; missing cases | **Fixed.** Exact amounts; explicit failure if no candidate; new cases for downgrade, omitted booking, withheld refund, wrongful booking, undercharge and change-not-made. The impossible double-refund test was replaced |
| 10 | Minor | Certificates are removed whole on booking; partial use is forfeited | **Documented** in the dollar_diff docstring. A missed booking's certificate is not double counted |
| 11 | Minor | Haiku defaults (adaptive thinking, effort medium) weren't in the fingerprint | **Accepted.** Added to PILOT_PLAN's rating cell |
| 12 | Minor | Expectations 2 and 5 are near-tautological | **Accepted.** They're kept as replay checks only, not as evidence |
| 13 | Minor | 99%/5% should be 2,654 (z = 2.576) | **Fixed** |
| 14 | Minor | The ρ evidence came from τ-bench retail on another model | **Accepted.** Labelled as indirect |
| 15 | Minor | `gold_and_agent_dbs` needs the full trajectory and omits solo_mode | **Documented.** No airline task has an initial state |

## Review 2 — after step 5 (dollar diff v2, collect.py), 2026-10-21
| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | Exact (payment_id, amount) matching makes the same end state by a different route or method look like loss (task 18 other card: $6,594; task 32 split vs combined: $510; task 19 upgrade-then-cancel: $1,226) | **Fixed (v3).** Net money is compared per paired reservation. A pure method swap is a $0 `payment_method_mismatch`. Tests: other card, combined change, upgrade-then-cancel |
| 2 | Blocker | Reservations paired by sequential ID (HATHAT…), so booking order or a wrong-then-correct booking reads as harm ($1,992; $1,790) | **Fixed (v3).** New reservations are paired by content (service, then route); existing ones by ID. Tests: booking order (synthetic and real task 23), wrong-then-correct booking |
| 3 | Major | A price difference on a shared booking was sized at the whole charge ($320 for $30 of unwanted insurance) | **Fixed.** Sized by net difference. Tests: insurance $30, missing bag fee $50 |
| 4 | Major | Certificates double counted or mislabelled (card instead of certificate: $1,196; certificate on a cheaper booking: $750; certificate at $0: $0) | **Fixed.** A certificate consumed by the agent but kept by gold = harm of face − applied. Only certificates absent from the initial DB count as compensation. Tests: real task 8 card-vs-certificate = $0; $125 forfeit; $250 full forfeit |
| 5 | Major | Real undercharges invisible because `nonfree_baggages` sat in the content key | **Fixed.** "Same service" is customer-facing (flights, cabin, passengers, total bags, insurance, status) |
| 6 | Major (omission metric) | Gold's own +X/−X pairs inflated omissions (task 7: $2,440 vs a true $296) | **Fixed** by netting. Re-scored task 7 = $296, task 32 = $114 (was $906) |
| 7 | Minor | Name case and list order changed the classification | **Fixed.** Casefolded, sorted. Test: name case |
| 8 | Minor | No regression tests for the above | **Fixed.** 40 tests (synthetic + real replays) |
| c1 | Minor | Judge cost omitted | **Documented.** About 1% of cost (10 judge calls in breadth). Not yet logged |
| c2 | Minor | >100K prompts billed at the normal rate | **Fixed.** Long-prompt rate applied (none occurred) |
| c3 | Minor | An unknown model crashed the collector | **Fixed.** Cost = None per row, never guessed |
| c4 | Minor | Language env kwargs not passed to replay | **Documented.** English only; the pack DB is identical to the default (reviewer verified) |
| c5 | Minor | Stratum still taken from gold actions | **Fixed.** Stratum = customer request type (cancel/book/change/compensation/info) from the scenario text; `gold_moves_money` kept separately |
| — | Rebuttal | "Task 42 $4,418 over-refund looks genuine; contradicts 0 insured events" | **Rebutted.** The reviewer reviewed money only, not policy. MFRB94 is business class (policy permits cancellation) and the customer explicitly requested it; `policy.py` classifies it as a permitted divergence. The claim of 0 insured events covers both batches after the policy layer |

## Review 3 — after step 7 (projection), 2026-10-21
| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | The N/ρ ceiling and the "per conversation" bound assume an unstated target population. For the 50 tasks themselves there is no ceiling. For real traffic the issue is bias. Variants are nested in parents | **Accepted.** PILOT.md now states the estimand and reports framing (a) the finite 50 tasks (option A ⇒ ≤0.3%) and (b) a large pool (ceiling), plus the nesting caveat and a proposed ρ_parent pilot. "Per conversation" removed |
| 2 | Major | The ICC proxy used reward failure, which includes COMMUNICATE-only failures (task 7 drives it) | **Fixed.** ρ is now the DB-mismatch ICC (breadth 0.42). Reward ICC is shown for comparison only. The range is propagated |
| 3 | Major | The 8% bound is a heuristic; the robust bound is 10.5% (pooled) | **Fixed.** Headline is ≤11.3% (breadth, tasks as units). The model-based 8.2% is secondary; the one-event alternative is 12.6% |
| 4 | Major | ICC uncertainty unreported; task bootstrap never called and flattens clusters | **Fixed.** `icc_bootstrap` preserves clusters: breadth DB ICC 95% (−0.12, 0.87). The claim now rests on "q small ⇒ max ρ ≈ 0.03", not on a point ρ |
| 5 | Minor/Major | The hand-picked batch was pooled, contrary to plan | **Fixed.** Estimates use the breadth batch only; pooled is shown as reference |
| 6 | Major | Cost extrapolation omitted task generation and validation, the recommended Sonnet simulator, the judge and rate limits | **Fixed** in projection.json and PILOT (Sonnet ≈ $0.055 per run; task generation flagged as the dominant excluded cost) |
| 7 | Minor | The design effect used the mean, not the weighted cluster size | **Fixed** (m_w = Σm²/Σm) |
| 8 | Minor | "2 runs per task" not derived; the minimum task count is ρ·eff | **Fixed.** The minimum is reported; ×1.4 at m = 2 |
| 9 | Minor | Option B labelled frequency but included CV² = 1 | **Fixed.** Frequency-only and pure-premium rows are separate |
| 10 | Minor | Table errors; "every failure was an omission" false; hand-off isn't a failure category | **Fixed.** 11 omission / 3 COMMUNICATE-only / 1 permitted commission |
| 11 | Minor | Wilson used z = 1.96 for a one-sided 95% bound; stats untested | **Fixed.** `wilson_upper_one_sided` (z = 1.645); 6 stats tests |
| 12 | Minor | User-caused failures still in ρ | **Open.** Only 1 user-caused case was identified (task 14, pilot batch, not in the estimation sample). Automate the attribution in the main run |

## Publication check — third-party name (2026-10-21)
A `.gitignore` comment in the first commit named a third party. It was removed from the tree, then the history was rewritten and force-pushed with Ishaan's approval. No branch contains it. GitHub still serves the orphaned old commit by exact SHA until its garbage collection runs. Ishaan chose **not** to delete and recreate the repo. If needed, a GitHub Support purge request is the remaining route.
