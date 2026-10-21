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

## Review 4 — after Goal 3 v2 phase 0 (simulator, technique validation), 2026-10-21
| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | The control variate used an oracle score with a known mean | **Fixed, and the verdict reversed.** The T4r pre-run task score uses an *estimated* pool mean (variance added) and cross-fitted β. At r = 0.3 or 0.6 there's **no gain** (runs ratio 1.00 / 0.99); only r = 0.95 gives 18%. Control variate dropped for phase 1 |
| 2 | Major | IS loses to sampling at W; "1.7×" was against a weak baseline | **Accepted and confirmed.** PROP and Neyman arms added: IS needs **1.20×** PROP's runs, oracle Neyman 0.91×, plug-in Neyman 1.03×. PROP is now the default; IS only for rare-stratum estimates |
| 3 | Major | Bühlmann as coded = post-stratification; credibility untested | **Accepted.** Tested where it bites (T2f, 30 fine workflows): MSE −69% to −91% vs raw. The naive EB interval under-covers (0.47–0.64), so it's flagged open. Coarse-strata T2 is relabelled "≈ post-stratification" |
| 4 | Major | Runs-to-±20% understated; parents bind; means hide worst cells | **Fixed.** Worst cell over parent share reported, plus runs **and** parents for 5×2, 1×2 and 1×1 designs. Pilot-like q = 2%: 13,011 runs / 1,301 parents (5×2) vs 3,232 / 3,232 (1×1) |
| 5 | Major | ICC grid is latent but was presented as observed; needs 0.8–0.9 | **Fixed.** Labelled latent, observed ICC reported, extended to 0.8/0.9. The pilot's 0.42 ≈ latent 0.8. "REL" renamed to logit offsets |
| 6 | Major | Near-miss generator was a strawman | **Fixed.** Poisson counts: unbiased with R known (29% fewer runs). With R calibrated from a separate 2,000-run sample: unstable (bias up to +39%). Verdict: **usable only with externally validated R**, not "drop" |
| 7 | Major | Pass rule missed upper-bound coverage, zero events, mix misspecification and width | **Fixed.** Upper95 coverage added (PROP 0.944). Zero-event arm q = 0.5/1% with a CP-on-parents fallback (upper95 ≥ 0.94). Mix-misspecification arm (−9.8% bias, cov 0.75). Worst cells reported |
| 8 | Major/Minor | Monte Carlo error made some verdicts unrobust | **Fixed.** 300 reps per cell; pooled coverage reported with MC SE (≈ 0.002–0.003) |
| 9 | Minor | Post-hoc changes not labelled | **Fixed.** "Post-hoc deviations" block added to EXPERIMENTS.md. Phase 0 v2 was pre-registered before any code change |
| 10 | Minor | Multinomial allocation left strata empty | **Fixed.** Fixed stratified allocation, ≥ 2 parents per stratum |
| 11 | Minor | Thin tests | **Partly fixed.** A numpy-int ICC regression test added (it found a real bug). The simstudy2 estimators are validated by the grid itself. A dedicated unit test of the zero-event fallback was added |

## Review 5 — after Goal 3 v2 phase 1 (E1, E1x, E2, E3, 1b), 2026-10-21
Fresh-context reviewer, repo only, no paid calls. It recomputed every cell rate, Δ_c, I_c, the Wilson/CP bounds and the E2 components from the CSVs, and **all matched**. The findings concern interpretation.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | The E1x soft rule needs overlapping CIs, but they're disjoint. The text falsely said "CIs overlap", and the code dropped the clause | **Accepted, fixed.** The statement is struck through and corrected: neither rule fires as written. The code's deviation is disclosed. The adopted reading is labelled a judgment: "ranking not shown simulator-robust; don't price off one simulator" |
| 2 | High | Δ_O rests on 3 tasks (sign test p = 0.25), and "P(same sign) = 0" is forced by construction. The robust signal is I_O. There are 21 contrasts | **Accepted, fixed.** Exact sign tests added for every contrast (`scripts/review5_checks.py`): no agent gap is significant, **I_O 6/0, p = 0.031**. Δ_O un-bolded, multiplicity note added |
| 3 | High | E2 42-v1_rename is a policy breach but about $0 counterfactual: business class could be cancelled for a full refund and rebooked | **Accepted.** Relabelled "policy breach, gross $1,606, counterfactual ≈ $0". **Insured loss is effectively 0 across phase 1.** The E3 "peril sits in complex changes" inference is withdrawn. Policy-layer extension (compare change refunds with the permitted alternative) is **open**, a phase-2 to-do |
| 4 | High | The mechanism claim rests on inconsistent Haiku labels | **Accepted; audited.** The blinded second model rater (33 runs) gives κ = 0.45. The O-specific mechanism **is not supported** (Sonnet-agent user_caused share is about 40% under both H and O). The claim is withdrawn; "consistent with" wording kept only for the date-invention fault. **The human audit is still open** |
| 5 | Medium | The shared H×H baseline ran at a different time and commit | **Accepted; pending.** A labelled sensitivity analysis replacing H×H with REF-H (and H×S with REF-S) runs when the reference run finishes |
| 6 | Medium | E2's V_eff was on the latent scale | **Accepted, fixed.** Observed scale: 1.58 (2 runs, CI 1.27–2.22) and 1.84 (1 run, CI 1.42–2.63; P(≥ 3) = 0.006). The verdict (not ≥ 3) stands |
| 7 | Medium | The pairing artefact also inflates omission | **Accepted, fixed.** Omission Δ_O is +0.06 without it; footnoted. Pairing v4 is to be a labelled sensitivity analysis only |
| 8 | Medium | Run-level Wilson intervals ignore clustering | **Accepted, fixed.** Cluster-bootstrap intervals added for every E1x cell and for E2 (variant failure [0.135, 0.37] vs Wilson [0.20, 0.30]) |
| 9 | Medium | Data untracked; McNemar code uncommitted; wrong timestamp; timing unverifiable | **Accepted, fixed.** Data and code committed (`144a3c9`, `ea5513c`), McNemar reproduced exactly. Timestamp corrected to 03:35:46. That E1x-SO started 2 minutes before the analysis commit is disclosed as unverifiable from git |
| 10 | Low | Hypotheses "confirmed" without a test | **Accepted, fixed.** E1 H4 → "not tested"; H1 → "consistent, not significant"; 1b-P2 → "untestable"; E2-P2 → "within noise" |

**Gate implications accepted from review 5:**
- **E3 is a ceiling result:** 160/160 generated refusal runs passed. Generated tasks must first pass a fidelity pilot, showing they fail like benchmark tasks, before any "thousands of new parents" phase 2.
- **Insured loss is about 0 in about 675 runs.** The link from DB mismatch (the sizing proxy) to insured loss is unvalidated, and is the main open risk.
- **Phase 2 needs ≥ 2 simulators, a simulator-fidelity audit and human-validated attribution.**
- **Added from the audit:** 55% of failures are task_ambiguous (benchmark gold issues on tasks 7, 32 and 44), so failure rate on τ² airline is a noisy proxy.
