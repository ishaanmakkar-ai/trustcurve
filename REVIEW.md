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
| 11 | Minor | Thin tests | **Fixed** (completed after phase 1). A numpy-int ICC regression test was added (it found a real bug), plus a dedicated zero-event-fallback test, E1x kill-rule tests and reference-estimator tests: 57 tests in all. The simstudy2 estimators are also validated by the grid itself |

**Review 4 follow-up (after phase 1, 2026-10-21):**
- #11 (thin tests) is now **fixed**: 57 tests, including a dedicated zero-event-fallback test (`test_simstudy.py`), E1x kill-rule tests (`test_phase1_e1x.py`) and reference-run estimator tests (`test_phase1_reference.py`).
- All 11 review-4 points are resolved or rebutted above.
- The phase-0 grid was rerun as phase 0 v2: 120 cells × 300 reps, `results/phase0v2/grid.json`, commit `b7f985e`.
- Review 3 #12 (user-caused failures in ρ, "open"): attribution is now automated (Haiku labeller) and second-rated (blinded, κ 0.45). On the breadth tasks, user_caused is 0–22% of Haiku-agent/Haiku-customer failures, and the E1 kill rule (≥ 30%) doesn't fire. ρ is therefore not materially setup-inflated. **Resolved, with the human audit as a stated open item.**

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

## Review 6 — reference run and its audits, 2026-10-21
Fresh-context reviewer, repo only. Every headline number reproduces. `phase1.reference` and the swap script predate the outcomes (git-verified).

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | Check 2's −30% is pooling: VHM is floored in 164/200 slices, weights 0.04–0.10, and the grand mean beats credibility (0.0106 vs 0.0113); out of sample the ratio is 1.01 | **Accepted, verified (same numbers), fixed in the prose.** Phase-0 verdict 3 qualified. EPV-floor scale bug noted (non-binding). GATE updated |
| 2 | High | Check 1 is uninformative for the rare-event regime (finite population, same data as truth, no zero-event slices); on 0.9% harm, coverage is 0.83 among non-zero slices | **Accepted, fixed.** Claim scoped to framing (a) at about 19%; the rare-event under-coverage is recorded. Validating rare-event intervals is a phase-2 prerequisite |
| 3 | High | The audit covered flagged runs only; one rater; no CI; consequential loss ignored; 29/4 mislabelled | **Accepted. Partly resolved:** all 8 unflagged over-refunds checked (all permitted); clustered CI added (0.34–2.4%); scope, consequential-loss and 29/4 caveats added. **Open:** a random audit of about 50 of the 147 other unflagged mismatch runs and a second rater. Both are folded into dollar-diff v4 validation (GATE step 1) |
| 4 | Medium | The baseline swap overclaims: Δ_O's CI is a sparse-bootstrap artefact; "contemporaneous" is wrong; designed after the fact | **Accepted, fixed.** "A reversal is not established"; I_O is the robust signal |
| 5 | Medium | Check 4 had no pass/fail criterion; the sign test was mis-stated; the effect is concentrated; "stronger" is interpretive | **Accepted, fixed** |
| 6 | Low | "About 4×" is 3.7×; check 1's band was weak by design | Noted; the 3.7× figure is shown alongside |

**Gate implications accepted:**
- Don't fund phase 2 yet.
- Loss frequency will be set by how many "trap" tasks a generator produces: 3 of 50 τ² tasks carry all the genuine harm. At about 1% with 1 run per task, 3,000 tasks give ±32%, and ±16% needs about 10,000.
- A cheap generated-task pilot (about 300 tasks) with dollar-diff v4 should come first.

## Review 6 — after Study 2 phase A (plus a pre-spend check of the phase-B code), 2026-10-21
Fresh-context reviewer, repo only, no paid calls. It re-ran slices of the simulation on fresh seeds and recomputed the tables. All loop-2 rows match the JSON. M1's loop-2 pass replicates (0.886 / 0.894). The beta-binomial, Gauss–Hermite θ and capped mean are correct. The review-5 #3 case scores exactly $0.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | **Blocker** | HAR-CF's confirmation call passes the conversation (which contains tool calls) without `tools=`. LiteLLM raises, tau2 re-raises, and errored runs are dropped downstream, so exactly the high-money runs vanish and HAR-CF is biased to 0. The harness test monkeypatched `generate`, so it missed this | **Fixed.** The confirmation question now gets the conversation rendered as text in one user message (as HAR-PC does) with the agent's own system prompt. A live 1-task smoke test of every harness configuration runs before any paid batch |
| 2 | High | Phase A's underwriting mix is not the real pool's (real: 45/23/3/18/1; the screening half has 0 "other"). With the real mix, **M1 fails the pass rule** (0.837 / 0.855). One "other" task makes M1's bootstrap degenerate for 10% of W | **Accepted. The M1 verdict is withdrawn pending phase-A loop 3** (pre-registered in STUDY2.md A3): the real pool mix and screening sizes, template clusters, configuration × stratum severity heterogeneity, a directional author shift, and a new candidate M1c (template-cluster bootstrap + sparse-stratum pooling) alongside M1 and M2 |
| 3 | High | Underwriting reason labels were wrong. V-43 and V-44 explicitly deny a health issue but were labelled `health`, so wrongful cancellations of insured bookings would score $0. The "uncertain" path was unreachable (a no-op in ledger.py) | **Fixed.** 13 V-task reasons were hand-labelled from scenario text only (`HAND_REASONS` in build_underwriting.py, with reasons). An `unknown` category was added. The ledger maps unknown or missing reasons to `uncertain` for insured cancellations |
| 4 | High | M1 under-covers the **upper** tail (R above the 95% bound 9.2% vs a nominal 5%), which is the side that matters for pricing | **Accepted.** Upper-95 coverage is now a headline metric, and loop 3's pass rule adds upper-95 coverage ≥ 0.92 (labelled as added after this review) |
| 5 | Medium | The HAR-PC checker truncates tool results at 700 characters. `insurance` falls past 700 in 49% of reservations. Unparseable replies count as blocks | **Fixed.** Tool results are passed in full to both checkers. Verdicts that can't be parsed are logged (`unparsed: true`) and counted in the harness summary |
| 6 | Medium | K2 doesn't fire on a NaN Spearman (all realised equal, e.g. all zero). Coverage includes trivial [0, u] ∋ 0 cases. The binomial CI treats configurations as independent | **Fixed in score_c (before any C outcome).** NaN Spearman → K2 "fires (undetermined)". K2 coverage is also evaluated on configurations with ≥ 1 realised event (fires if < 0.70 when ≥ 5 such configurations). The coverage CI is a task bootstrap |
| 7 | Medium | The loop-2 fix mirrors the DGM's own severity structure | **Accepted, stated as a limit.** Loop 3's DGM uses configuration × stratum severity heterogeneity instead |
| 8 | Medium | 40 of 90 underwriting tasks come from 3 templates, but the bootstrap treats them as independent. The spec makes experience tasks harder (a directional shift); S2 was symmetric | **Accepted.** Loop 3 adds template clusters to the DGM, a cluster bootstrap (M1c) and a directional-shift scenario (R6, +0.5 logit) |
| 9 | Medium | A secondary dollar-diff error dropped the whole row, primary commission included | **Fixed.** `collect2` writes `dd_error` separately; primary filtering uses the ledger `error` only |
| 10 | Low | Usage of blocked agent generations isn't counted | **Fixed.** Logged in harness.jsonl and priced in `harness_cost` |
| 11 | Low | ρ isn't tested (DGM ICC 0.01–0.17 vs the assumed 0.5) | **Stated.** The reviewer's sensitivity analysis shows predictive coverage of 0.882 / 0.894 / 0.902 at ρ = 0.05 / 0.5 / 0.9 |
| 12 | Low | Ledger edge cases: a certificate issued before the change/cancel scored in full; changes on another user's reservation counted only refunds; cancel+rebook ignores bags and insurance; the certificate/gift-card breach in B2 is not implemented | **Fixed:** certificates are judged after the whole run (touched set complete); a change on another user's reservation is priced at the full money moved. **Documented (labelled deviation from B2):** cancel+rebook ignores bags and insurance; payment-method rule breaches aren't priced (they move no money) |
| 13 | Low | "Rare events cost discrimination, not calibration" is misleading: in S5, M1's median bias is −14% / −43%, its PIT deviation is 0.21 / 0.35, and the point is usually 0 | **Accepted, reworded** in STUDY2.md |
| 14 | Low | Phase A wasn't rerun on the final code | **Resolved by loop 3**, which runs on the final code |

## Review 7 — after Study 2 phase B (pilot, screening, gate decisions, power), 2026-10-21
A fresh-context reviewer replayed the ledger on all 1,685 pilot and screening runs. It matches the CSVs, except one run capped at $2,000 by design. The reviewer read all 9 commission events: every one is genuine. It found no missed commission among the 21 runs where dollar diff shows severity but the ledger shows $0. Costs reconcile within $0.03 per batch.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | **Winner's curse.** KB-\*, CAP-H4 and H4-HPC were added because the 45 screening (= underwriting) tasks showed events, so their forecasts start high. The power gain from 0.18 to 0.33 is partly selection. H4-HPC's truth was copied from CAP-H4. M2 pools across configurations, so additions move the 13's forecasts | **Accepted (phase-C pre-registration):** **K2 is scored on the pre-registered 13 only**, with M2 fitted on those 13 alone. Every added configuration is forecast **from the unseen second underwriting half only** (no selection data), and reported as an extended set. **H4-HPC is dropped.** The B-L2-sanctioned **H4-KB** (Haiku 4.5 + wrong rule) replaces it |
| 2 | High | **G3 inconsistency / confound.** Underwriting's Haiku simulator failed G3, and underwriting and experience differ in author, simulator and date hint at once. The G3 counts are tiny (Sonnet 0/4, CI up to 0.53). pilotD-B0-S was labelled twice | **Accepted.** Phase C adds a **bridge arm**: the Haiku-5.5-family configurations and CAP-H4 also run a 60-task experience subset under the **Haiku simulator with the date hint**. That separates "different tasks" from "different simulator" for RQ5 and for any K2 firing. Gate CIs are reported. The double labelling is disclosed (an identical rerun: the second overwrote the first) |
| 3 | High | **G1 loop count overstated** (1 of 2 loops run). X3p-036's gold is wrong: the booking was made 20.9 h earlier, so cancelling was permitted, and B0 was marked failed for getting it right | **Accepted.** STUDY2 corrected to "1 of 2 loops". X3p-036's gold is fixed and v3p's G1 recomputed (2/40 = 5.0%). **Ishaan chose to run the second difficulty loop as pre-registered.** If G1 still fails, K3 fires and the study ends with that negative result |
| 4 | Medium | The power truth model creates ties by construction (pseudo-counts, sample size). The KNO-WR family's risk is one trap task. No directional shift was simulated | **Accepted.** The power analysis is re-run before C with truth drawn from the posterior per replication, a shared trap-task structure within families, a +0.5 directional scenario, and only underwriting-simulator runs |
| 5 | Medium | The first B5 table (M1, width ≈ 1e7) wasn't marked superseded. `score_c` sharpness divides by the point. The coverage arm of K2 has little power because intervals are 6–8 × θ | **Fixed.** The table is marked superseded. Sharpness now uses width / max(point, realised, $1). STUDY2 states that K2's coverage arm can hardly fire, so the Spearman arm carries K2 |
| 6 | Medium | KNO-WI left the Travel-insurance line ("full refund … health or weather") in place, so the variant contradicts itself. KB-CAPS ran on screen30, which excludes V-1 (the only KNO-WR trigger) | **Fixed.** Both insurance lines are edited and KNO-WI is re-screened. KB-CAPS's direction is marked untested at screening |
| 7 | Medium | `score_c` bootstraps over shared tasks, but independent per-configuration samples would intersect in ≤ 50 tasks or none | **Fixed.** Experience samples are **nested and stratified** (50 ⊂ 100 ⊂ 150 ⊂ 260 by a seeded order), frozen with the forecasts |
| 8 | Low | Ledger: the reason is recorded per task, not per reservation; unrequested cancellations aren't scored; `breach_kinds` is noisy | **Documented** as known gaps in STUDY2. `breach_kinds` is relabelled "zero-loss policy breaches (diagnostic)" |
| 9 | Low | Phase B was $44.60 (1.12 × $40); the S0 "≈ $87" vs the $83 baseline; the judge, retries and agent-authoring work are unpriced | **Corrected** in STUDY2: phase B $44.60; baseline $83.00 (reconciled). The tau2 judge is ≈ 1% of run cost (Goal 3 estimate) and carried as a +1% line. Authoring, audit, review and planter agents ran in Claude Code, not on the API keys |
| 10 | Low | The date hint applies only to experience; it cut luna's failure rate from 21% to 9% | **Folded into #2:** the bridge arm runs the Haiku simulator *with* the hint on experience tasks |

## Review 8 — after Study 2 phase C, 2026-10-21
A fresh-context reviewer recomputed every headline from the run CSVs and frozen forecasts; all match `score_c.json`. **The freeze is clean:** the hashes match commit `765599e`, the first experience log came 16 s after the freeze commit, and the ledger, collector, forecast code and experience meta are unchanged since. **The pre13 K2 firing holds.** Four interpretations were overstated. All corrections are post-hoc readings (`scripts/study2/posthoc_c.py`, `results/study2/phaseC/posthoc_review8.json`). The frozen primary is unchanged.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | Pooled-24 ρ = 0.55 is mostly group membership. An "extended vs pre13" indicator alone gives ρ = 0.61. The pre-registered "extended" group is the 11 additions: ρ 0.75, coverage 9/11 | **Accepted.** Headlines are now within-group only: **pre13 ρ 0.006 (K2 fires); ext11 ρ 0.75 [0.53, 0.77], coverage 0.82.** The pooled-24 figure is reported only alongside the indicator baseline, and labelled as not a forecast measure |
| 2 | High | The extended CI (0.15–0.53) was a bootstrap of a different statistic (the first 50 shared tasks, where the point is 0.27), not a sampling artefact | **Accepted.** Relabelled. A post-hoc Poisson bootstrap over each configuration's own tasks (paired on shared tasks) gives pre13 [−0.41, 0.22], ext11 [0.53, 0.77], all-24 [0.35, 0.64] |
| 3 | High | "The checker removes ~98%" is partly by construction: the checker sees the *correct* policy (an oracle). Omission rises (+$13.9), so the net saving is ≈ $8 | **Accepted.** Restated: an **oracle** policy checker removes stale-rule commission ($22.0 → $0.4) but raises omission ($27.7 → $41.6). Net ≈ $7.8 per conversation. A checker with the stale policy is untested (a Study 3 item) |
| 4 | High | "The underwriting simulator elicits less risk" is unsupported: events H 32 / S 40 / L 30 over 1,200 paired cells. The subset was chosen post-hoc and is driven by CAP-H4 | **Accepted.** Paired exact tests: H vs S 14:22 discordant (p = 0.24), H vs L 16:14 (p = 0.86). **C-P5 is inconclusive**, with no detectable simulator effect at this n. The bridge also used the date hint, unlike underwriting |
| 5 | Medium | KB-CAPS and CAP-S/INT-2 were compared on different task sets. On the same 50 tasks KNO-WR is $14.6 vs KB-CAPS $16.3, so the direction reverses. B0 is $40 on the first 50 tasks (X2a-059) | **Accepted.** Shared-task comparisons replace them. The KB-CAPS < KB direction is **refuted** on shared tasks. CAP-S and INT-2 vs B0 on the 50 tasks: $0 vs $40, driven by the single X2a-059 event |
| 6 | Medium | The C-P4 ratio range was wrong (H4-KB 4.0×); "every risky configuration" selected on the outcome. **The HARD2 addendum, written after KNO-WR was the only risky base, asks for 25–30 h bookings, exactly where the 72 h rule bites** | **Accepted, and stated as a design limitation of this study.** The ratio is corrected to up to 4.0×. "Risky" is now defined by forecast: among configurations forecast ≥ $12, the ratio realised/forecast is 0.03–4.0 (KB-HPC, CAP-L and KNO-WC are over-forecast). **Realised stale-rule loss is partly a function of how densely the experience authors wrote 24–72 h traps**, so its level is not a deployment estimate |
| 7 | Medium | No multiplicity correction, and few independent events | **Accepted.** With Holm correction over 23 contrasts, only **CAP-H4 (+$55.8, p_holm 3e-4) and H4-KB (+$76.1, p_holm < 1e-6)** survive. Realised events fall on 13 distinct tasks (pre13) and 36 (extended). CI and p are reported together |
| 8 | Medium | Flown-segment pricing overstates levels | **Accepted.** Variant: flown-segment cancellations priced at the flown legs' value only (53 runs changed). pre13 ρ 0.003; ext11 ρ 0.75, coverage 0.91. B0 → $9.75. Ranking is unchanged and levels drop about 10–20%. The human audit remains the real check |
| 9 | Low | `booking_on_other_account` is customer harm, not airline payout | **Accepted.** Removed from the commission variant in #8 (a separate peril) |
| 10 | Low | Charts mix 150- and 60-task bars; some points are unlabelled; the title shows the pooled ρ | **Fixed post-hoc:** `scripts/study2/fig_phaseC_v2.py` (same-task bars, every point labelled, within-group ρ in the title). The frozen figures are kept unchanged |
| 11 | Low | "No run before the freeze" rests on filesystem timestamps | **Recorded:** first experience log `exp-B0-S.log` created 16:45:55 BST; freeze commit 16:45:39 BST. Runner guard: `run_phaseC_exp.sh` refuses to start without the hash in a commit message |
| 12 | Low | The judge line and agent labour are not in spend.csv | **Accepted:** +1% judge ≈ $2.4 noted. The authoring, audit and review agents ran in Claude Code, not on the API keys |

## Review 9 — after Study 2 phase D and the write-up, 2026-10-21
A fresh-context reviewer verified the blinding:
- The seal recomputes to `327e358f…`, committed at 06:53, before any D run.
- The blind report (`2cad9047…`) was written and committed 7–9 s before `unsealed.json` was written, and its flags come from code committed earlier.
- The fault module behaved as specified: realised per-opportunity rates were 0.28 / 0.13 / 0.27 against planted 0.30 / 0.10 / 0.25.
- All 8 figures regenerate **byte-identically** from HEAD.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | `unseal_d.py` double-counted: one `draw` line plus one `applied` line per firing. True opportunities/firings are D1 173/48, D3 174/22, D5 11/3 | **Fixed** (counts `draw` only); re-run. Mutation score unchanged (flags come from the blind report). The D table is corrected in STUDY2 |
| 2 | High | D1 overstated: the agent retracts the inserted sentence in ≥ 35 of 48 fired conversations, so ≈ 13/90 end with an uncorrected misstatement. The fault is invisible only to the action ledger | **Accepted.** Reported as fired 48 times (in 53% of tasks), with about 13 uncorrected (reviewer's transcript count). Self-correction is an artefact of injecting into the agent's own context, now listed as a limitation |
| 3 | High | K4's headline misattributes the misses: D2 and D6 had 0 opportunities (untested), and D5 had 3 firings (no power) | **Accepted.** K4 fires as pre-registered (0.20). Exposure-conditional scores are reported alongside: 1/3 among exercised faults, 1/2 among faults with any power. The headline is reworded: "the eval missed what it didn't exercise; only an action-level ledger with exposure catches faults" |
| 4 | Medium | Deviation: the pre-registration named the M1 lower bound; the code used M2 (fitted on {B0, D1–D6}) | **Labelled post-hoc** in STUDY2. Outcome unchanged (D3 is flagged by the sign test, p = 9.5e-7) |
| 5 | Medium | Blind recovery compared per-task incidence, not the planted rate | **Restated:** per-task event incidence 0.222 vs firing incidence 0.244. 19 of 22 fired tasks produced a ledger event; 1 event (E3B-3) came from no firing. Per opportunity: planted 0.10, realised 0.126 |
| 6 | Medium | "The agent never issued a certificate" is false (1 call in 630 underwriting runs) | **Accepted.** Reworded to "rarely (1 in 630 runs)", against 11–12% of experience tasks (B0 issued certificates on 18/150 and 16/150) |
| 7 | Medium | D-P2 and D-P1 for D2, D5 and D6 are untested, not confirmed or refuted | **Accepted** and relabelled |
| 8 | Medium | "Repricing cuts levels 10–20%" is wrong: it's 0–44% (≈ 25% typical), and ext11 coverage moves from 0.82 to 0.91 | **Fixed** in E |
| 9 | Medium | ext11 ρ 0.75 is post-hoc and unlabelled; without the two H4 configurations ρ = 0.55 (p = 0.125, n = 9, verified) | **Fixed** in E: labelled post-hoc, with the leave-out figure |
| 10 | Medium | "Phase A predicted exactly this (R6)" overclaims (R6 kept the ranking), and K1 omits the M1→M2 history | **Fixed** in E |
| 11 | Medium | The spend table was stale (phase B $46.73) | **Fixed** from spend.csv: B $46.73, C $237.01, D $6.88, total **$373.63** |
| 12 | Low | Missing limitations: 1 run per task in D; planter-defined opportunities; context injection; the bridge's date hint; the Haiku simulator failed G3; G1 passed by 1 task under Haiku | **Added** to E |
| 13 | Low | Author count (6 main + 3 burned = 9) | **Fixed** (the vault log said 7, now corrected) |
| 14 | Low | The human label check was listed as met | **Fixed:** marked pending |
| 15 | Low | "Intervals 3–8×": the observed median relative width is 3.0 (pre13) and 2.5 (all 24) | **Fixed** |

## Review 10 — after Study 3 phase A′ loops 1–3, 2026-10-21
A fresh-context reviewer:
- regenerated every A′ table and decision file **byte-identically** from the committed JSON;
- recomputed one cell of each simulation from source, each matching exactly;
- found the decision rules applied literally, with STUDY3.md's numbers matching the tables.

The problems are in interpretation.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | "Pricing superiority not testable" is an artefact. A perfect check forecaster (true expected loss) has median \|log error\| 0.27 against F1's 0.40, so H3 (≤ 0.20) is unreachable for anyone. With F1's triggers at 0.3·q (bias ≈ −0.78 log, near Study 2) H3b power rises from 0.06 to 0.62 | **Accepted.** The claim is withdrawn and restated as "not testable **if** F1 is representative". Loop 4 adds the check forecaster to every cell and judges decidability against its ceiling. The RQ2 test-vs-estimation decision is deferred to loop 4 |
| 2 | High | F2's representative tasks are representative by construction too | **Accepted.** Loop 4 shifts F1's and F2-representative's trigger prevalence independently |
| 3 | High | H2 is close to decided by design (P = 0.98–1.00 at R = 3). About half of Study 2's real effects sit below the simulated rate range | **Accepted.** Proposed primary RQ1 test: the **exposure-matched paired McNemar test** (F2 vs F1, both at R = 3), with H2 reported alongside. It goes to Ishaan because it changes a plan hypothesis. Loop 4 runs triggers at both rate ranges and reports detection-vs-rate curves |
| 4 | High | Design is confounded with exposure (F2 at 300 rows vs F1 at 90) | **Accepted.** Loop 4 and the real design run F1 at R = 3, reported matched and unmatched. Headline (a) is restated as applying to the matched contrast only |
| 5 | Medium | The sign-test unit was runs, but S0 says tasks | **Accepted.** The per-task sum across runs is primary, as S0 says; run level becomes a sensitivity. Loop-3 claim (b) is withdrawn pending loop 4 |
| 6 | Medium | The 94.5% figure describes Study 2's own sandbox, fault catalogue and ledger (no statement peril). The 2.3% vs 1.2% figures compare different sets | **Accepted.** Reworded in STUDY3.md (correction note). The "pricing headroom is small" inference is dropped |
| 7 | Medium | Deciding RQ4 from F2-vs-F1 results is a non sequitur | **Accepted.** RQ4 is descriptive with intervals on its own grounds (3–5 underwriters, "indicative" in the plan), not because of A′ |
| 8 | Medium | RQ3 at 4 designed configurations is imprecise (SD 0.13–0.24) and conflates type mix with anticipation | **Accepted.** RQ3 is redefined as a difference-in-differences (F2 gap − F1 gap, exposure-matched), reported as an estimate with an interval. H5 is descriptive |
| 9 | Medium | The n_e rule used F2 pooled after the split was adopted (with the split it gives 100). The split's 40-task pricing arm prices worse than F1 at R = 1 | **Accepted.** Loop 4 sets n_e by a power criterion at a Study-2-calibrated point, against the ceiling. The split's pricing arm (40 tasks × R = 3) is pinned in the F2 spec |
| 10 | Medium | Git proves commit order, not authoring order. The loop-1 "clarification" first appears with the loop-1 results | **Accepted.** The clarification is relabelled post-hoc. From loop 4 on, each pre-registration is committed **alone**, and the code commit cites its hash |
| 11 | Medium | False positives were barely tested (n = 1 clean-vs-clean), and loop 3 recorded neither false positives nor coverage | **Accepted.** Loop 4 uses 4 clean controls (3 comparisons against the reference) and records false positives and coverage |
| 12 | Medium | The design costs $246–285+ against ≈ $126 left. The formula omits the judge, κ validation, planter, pilot and retries | **Accepted.** A full cost table goes to Ishaan before B′ |
| 13 | Low | Some rule cells were chosen in code. φ was evaluated on 100 trap tasks. "Not evaluable ⇒ fires" is post-hoc | **Labelled** in STUDY3.md |
| 14 | Low | The deployment rate is min(q, r) for about 20% of flaws; F3 counts any event; "below ~0.15" wording | **Fixed** in wording. Loop 4 draws r ≤ q, so the deployment rate is exactly r |

## Review 11 — after Study 3 phase A′ loop 4 and the closing summary, 2026-10-21
A fresh-context reviewer found that:
- sim_a4 implements pre-registration 9bbf26c faithfully;
- one recomputed cell matches sim_a4.json exactly;
- the cost arithmetic checks out;
- the decision rules were applied literally;
- the per-slice choice of C2 changes nothing (every slice picks ρ1 = 0.3).

The closing summary overclaimed and left items off the PI list. Resolved by the **revised closing summary** in STUDY3.md, which replaces the first version (kept above it, with a marker).

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | High | When F1 is representative, the F2-vs-F1 detection comparison can't be decided: matched McNemar power is 0.35 (0.17–0.45 across ρ2). The generic F1₃ itself passes H2 63% of the time, so "H1/H2 decidable" says nothing about design. The RQ1-form decision was missing from the PI list | **Accepted.** Added to "cannot decide" and to the PI list |
| 2 | High | ρ1 and ρ2 are partly set by whoever writes the experience scenarios. Writing F2's representative arm "to deployment frequencies" needs knowledge of that mix | **Accepted.** PI list: freeze the experience-scenario generator before F2 is built; its author must be independent of the F2 builder; the representative arm is drawn from the frozen generator by a third party. This is stated as making F2's pricing advantage partly true by construction |
| 3 | Med-High | One ρ1 can't match both Study 2's bias (ρ1 ≈ 0.3) and its Spearman (ρ1 ≈ 0). C2 is a near-tie, and interpolating gives ρ1 ≈ 0.45 with H3b ≈ 0.1–0.15 | **Accepted.** H3b at the calibrated point is reported as "≈ 0.04–0.25, bracketed by grid points". "As in Study 2" is replaced with "the simulation cannot locate Study 2's world on this grid" |
| 4 | Medium | "H3 not unreachable" takes a maximum over ρ1, a choice made in code. At C2, O's P(H3) is 0.16 | **Accepted.** Restated as "unreachable even for a perfect forecaster unless ρ1 ≈ 0"; the slice choice is labelled |
| 5 | Medium | The quoted ranges were selective (the ρ2 = 0.3 cell and the narrow rate range were left out) | **Fixed:** full ranges quoted |
| 6 | Medium | P ≥ 0.94 for H1/H2 holds only at r ∈ [0.05, 0.4]. At [0.02, 0.15], P(H2) = 0.69–0.72 and P(H1) ≈ 0.64–0.71 (reviewer's unregistered check, 200 reps), which is undecidable. Loop 4 never computed P(H1). The planted rates largely decide H2 | **Accepted** and stated. The P(H1) value is cited as the reviewer's check |
| 7 | Medium | A Wilcoxon signed-rank test gives H3b power 0.56 at C2 (ceiling 0.96), against 0.25 for the sign test (unregistered check) | **Listed for the PI** as an unregistered lever. It needs its own pre-registration before B′; A′ does not adopt it |
| 8 | Medium | Missing from the PI list:<br>• the RQ3 difference-in-differences redefinition (a change to a plan RQ);<br>• that no simulated design is affordable at ≈ $126, while loop 4's K1′ ignores affordability;<br>• cost levers: F1 at R = 3 is ≈ $63 for a power-0.35 contrast; the n_e = 200 rule fell back to its default;<br>• the $25 fixed cost and the judge price are guesses | **Added** to the PI list. S0's K1′ (affordability) is put to Ishaan instead of being declared |
| 9 | Low-Med | "The bottleneck is the precision of F2's arm" is unverified, and the ceiling caps power at 0.79 | **Reworded** as a hypothesis, with the ceiling noted |
| 10 | Low | Under-representation (ρ2 = 0.3) destroys the advantage, not over-trapping | **Reworded** |
| 11 | Low | O leaves out the statement judge and forecasts the mean | O is called an **approximate** ceiling. A judge-aware O changes nothing material (ceiling 0.19 → 0.26 at ρ1 = 1) |
| 12 | Low | False-positive maximum over all 96 cells is 0.027; the rate curve pools all ρ2 and r ranges; choices made in code were unlabelled | **Labelled** |
| 13 | Low | Authoring order is mitigated, not proven. "Exposure-matched" is 300 vs 270 task-runs | **Accepted.** Wording changed to "approximately matched" |

## Review 12 — after Study 3 phase B′ (infrastructure), 2026-10-22
A fresh-context reviewer, who opened no sealed content:
- recomputed every seal and pool hash, and all match;
- confirmed the flaw seal predates any benchmark run (none exists yet);
- reproduced the pilot numbers;
- ran the 18 Study 3 tests, which passed.

It found two loss-accounting defects and several blinding and pre-registration gaps.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Critical | ledger3's cut-off rule made withheld refunds impossible to record, because every τ² run ends on the customer's ###STOP### | **Fixed.** `is_cutoff` now requires an affirming final message that directly answers an agent request to confirm or proceed. Tests use realistic STOP endings, and G-trunc uses the same function. Re-checked on Study 2 B0: all cut-offs and transfers are uncertain, and the one primary event was read (genuine) |
| 2 | High | Missing harm kinds: fare and cabin overcharge on changes and bookings | **Fixed:** `fare_overcharge`, `cabin_upgrade_unrequested`, `withheld_change_refund`, with tests. Labelled a pre-data correction |
| 3 | High | The card map could be rebuilt from the committed seed and the public roster | **Fixed.** Cards were redrawn with a secret 128-bit seed, sealed with the mapping (new seal `5661742f…`) |
| 4 | High | The repo is public; efd4ef7's quotes are permanent | **Put to Ishaan** (make the repo private until D′?). Recorded as a limitation. efd4ef7 is on the attestation list |
| 5 | High | The F2 kit's do-not-open list was incomplete and out of date | **Fixed.** The kit is rewritten as an allow-list with a freeze attestation. STUDY3 §C′0 pre-registers the designer-exposed H2 primary set (X + M, 8 configurations) |
| 6 | Med-High | No 3-peril forecast or detection pipeline pre-registered | **Pre-registered** in §C′2–C′4 (code is written before any F1/F2 run): perils, caps, primary total, events, secondary failure flag, E7's role, the statement-excluded variant |
| 7 | Med-High | Nobody had checked that the flaws fire | **Done:** blind replay (`replay_faults.py`, $0, no keys in the environment). All 12 modules are clean. D4 and M3 (Study 2 conversations), and D1, D2, D4, X3 and M3 (Study 3 pilot), never fired. **Exposure-conditional H2 pre-registered** |
| 8 | Medium | Judge: temperature, batch path, parse failures, totals | **Fixed.** Totals are computed in code (caps and de-duplication) with tests; a "missing" rule; a Batch API path at 50% pricing. The temperature deviation is labelled: Haiku and Sonnet 5.5 reject non-default sampling |
| 9 | Medium | Spend-guard races and fail-open | **Fixed:** a file lock, cumulative recomputed from all rows, collection failures book the projected cost, C′ batches run one at a time |
| 10 | Medium | Stale budget mixing scenarios | **Recomputed** with pilot-measured costs and N4 = gpt-4o-mini: **≈ $377 with a Haiku judge, ≈ $511 with a Sonnet batch judge**, both under the $540 gate. F2 trap tasks are capped at 70 |
| 11 | Medium | No F2 freeze protocol | **Pre-registered** (§C′0): meta fields, validator, hash, drop-never-edit, no runs before the freeze, E7 merge |
| 12 | Medium | F3 transcript selection; designer-known matching rule | **Fixed:** F3 task IDs are fixed by seed and committed before any F1 run (`f3_transcript_ids.txt`). A blind matching rule for designer-known types at D′ is pre-registered (§C′6) |
| 13 | Medium | Contradiction about pilot tasks; sampling undefined | **Resolved:** the pilot tasks are excluded (the later correction governs). 200 tasks from the 380, disjoint Sonnet and luna halves, and the order are pre-registered (§C′5) |
| 14 | Low-Med | The G-trunc code didn't match its definition; not measured for the Haiku customer | **Fixed:** it uses `is_cutoff`, and the luna pilot result is unchanged (4/40). The Haiku underwriting customer is 1.5% on 585 Study 2 runs (passes) |
| 15 | Low | Housekeeping | B′ check 5 (G1) is recorded as **unmet**. Commits 703610c and a8342ef mixed pre-registration text with code; both were before any paid call (**labelled**). The policies README was updated for N4. The commission audit pack is Study 2's. An `unrequested_bags` test was added |
| 16 | Low | Process-global state; exec of the LLM-written module with keys in the environment | **Documented:** one configuration per process (`run_config3.py`). Replay ran without API keys. C′ runs need keys for the agent itself, and a module that exfiltrates them would be visible in the code read at D′. This residual risk is accepted and noted |
