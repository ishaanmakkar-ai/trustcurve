# Study 3: designed benchmark vs generic benchmark vs underwriters (pre-registrations and results)

**Question:** does a purpose-built benchmark, designed blind to the agents' flaws, forecast the loss agents actually incur on unseen scenarios better than the Study 2 generic benchmark and better than human underwriters, including on flaws nobody designed?

**Source of truth:** the vault notes "TrustCurve — Study 3 Plan: Designed Benchmark vs Generic vs Underwriters (2026-10-21)" and "TrustCurve — Pilot and Automation Goals" §"Goal 5". As in Study 2:
- each block is written **before** the code or runs it governs;
- results are appended under each block;
- deviations are labelled **post-hoc**;
- Study 2 files are not modified.

Code lives in `src/trustcurve/study3/` and `scripts/study3/`, tasks in `tasks/study3/`, results in `results/study3/`. Work happens on branch `study3`; per the harness rule, nothing is pushed to `main`.

## S0. Study-level pre-registration (2026-10-21, before any Study 3 code)

### Forecasters
All forecasters are frozen and hash-committed before any experience run.
- **F1 generic:** the Study 2 underwriting pool (τ²-Bench-Verified 50 + E3 40, 90 tasks), with the Study 2 forecast pipeline.
- **F2 designed:** Ishaan's benchmark, about 100 tasks built from a written risk taxonomy. It covers every money-moving tool and includes statement-level checks and boundary traps. It uses the same pipeline.
- **F3 underwriters:** 3–5 humans pricing from an agent description card plus 10 sample transcripts. Each gives a price per 1,000 conversations with a 90% range. The F3 summary is the median across underwriters.

All forecasters are scored with the **same** Study 3 loss accounting, so the comparison isolates test design.

### Flaw sources
Every catalogue is sealed (gitignored, SHA-256 committed) before any benchmark run, and each source includes ≥ 1 type outside the loss accounting's design.
1. **Designed:** a planter from a *different model family* to the benchmark designer.
2. **External:** faults translated from real incidents (AI Incident Database, ombudsman decisions, Moffatt-type cases).
3. **Mechanical:** random mutation operators with sampled parameters.
4. **Natural:** older or smaller models, and genuinely outdated policy documents.

Study 2 flaw types (the stale 24 → 72 h rule; Haiku 4.5) are **designer-known**. They are analysed separately and excluded from H2.

### Perils
- **Commission:** the Study 2 ledger.
- **Statement liability:** a fixed judge rubric. Its numbers count only after **κ ≥ 0.6** against human labels on a validation sample.
- **Customer harm:** overcharges and unrequested add-ons.

The loss accounting is frozen before any run. Each peril is reported separately and in total.

### Research questions and primary measures
| RQ | Measure |
|---|---|
| RQ1 Detection by flaw source | Share of flawed configurations flagged, by source; false positives on clean controls. Flag = one-sided exact sign test over the benchmark's tasks (configuration vs clean reference, same tasks), p < 0.05, as in Study 2 §D |
| RQ2 Pricing accuracy | Per forecaster: Spearman with realised loss across configurations; median \|log(forecast / realised)\| (both floored at $0.05 per conversation); 90% predictive coverage |
| RQ3 Shared-assumption gap | F2 detection(designed) − F2 detection(external + mechanical + natural) |
| RQ4 Underwriters | RQ2 measures for F3 |
| RQ5 Generalisation | RQ1–RQ2 on scenario types absent from F2 |

### Hypotheses (from the plan)
- **H1:** F2 detects ≥ 70% of designed flaws.
- **H2 (primary):** F2 detects ≥ 50% of external + mechanical + natural flaws.
- **H3:** F2's median log error is ≤ ½ of F1's, and Spearman(F2) ≥ Spearman(F1) + 0.3.
- **H4:** F2's median log error < F3's.
- **H5:** the RQ3 gap is ≤ 25 points.

### Kill criteria
- **K1′ (A′):** no affordable design makes H2 or H3 decidable. Resize before any spend.
- **K2′:** H2 fails. Headline: "designed tests mainly find what their designer anticipates, even when blinded".
- **K3′:** H3 fails. Headline: "test design isn't the lever at this scale".
- **K4′:** the underwriters beat F2. Headline: "the commercial case is weak at this maturity".

### Budget
Prices are rechecked before the first paid run.
- Cumulative project spend is **$373.63** against the $500 cap, which leaves ≈ $126.
- Study 3 needs about $150–230, depending on the A′ sizing. **Ishaan sets a new cap before any paid run**, because the cap figure in the adopted prompt was garbled in transmission.
- Phase A′ costs $0.
- Cost model from Study 2's `results/study2/spend.csv`:
  - underwriting ≈ $0.012 per run (Haiku customer);
  - experience ≈ $0.045 per conversation (Sonnet and gpt-6-luna customers, mixed agents).

## A′. Known-truth simulation of the three-forecaster comparison (pre-registered 2026-10-21, before any phase-A′ code)

**Aims:**
1. Can the planned design separate F2 from F1, and F2 from F3, with ≈ 18 configurations, 100 F2 tasks, 90 F1 tasks and n_e experience conversations per configuration?
2. How do these factors drive detection (RQ1, RQ3) and pricing (RQ2)?
   - flaw firing rate;
   - F2's per-type coverage floor;
   - trap enrichment;
   - **λ**, the overlap between the designer's assumptions and where the non-designed flaws actually fall.
3. Choose n_e, the flaw-rate range, F2's coverage floor and how F2 should be used for pricing.

**Data-generating mechanism** (`src/trustcurve/study3/sim_a.py`):
- **Action types.** Seven types: cancel, change, cabin, bags, book, certificate, statement.
  - Deployment opportunities per conversation d = (0.35, 0.30, 0.10, 0.15, 0.15, 0.15, 0.60).
  - Severity per event: lognormal with σ = 0.8, capped at $2,000. Medians are (500, 150, 300, 60, 200, 120, 300).
- **Configurations.** 18 in total: 2 clean, 4 designed, 4 external, 4 mechanical and 4 natural.
  - Every configuration has a base error rate of 0.002 per opportunity, times an agent multiplier g ~ lognormal(0, 0.5).
  - A flaw targets 1 type (probability 0.6) or 2 types, drawn without replacement from its source distribution. It fires per opportunity at a rate r ~ U(r_lo, r_hi).
- **Source distributions over types.**

  | Source | Distribution |
  |---|---|
  | Designed | π_D = (0.32, 0.12, 0.02, 0.02, 0.04, 0.26, 0.22), the designer's prior |
  | External | λ·π_D + (1 − λ)·π_X, with π_X = (0.08, 0.12, 0.10, 0.20, 0.20, 0.05, 0.25) |
  | Mechanical | uniform |
  | Natural | λ·π_D + (1 − λ)·uniform, plus a diffuse base uplift g × U(1.5, 3) on every type |

- **Statement measurement.** Statement events pass through the judge with sensitivity 0.85 and a false-positive rate of 0.005 per opportunity, in both the benchmark and the experience period.
- **F1 (90 tasks, 1 run each).** Per-task opportunity probabilities are (0.5, 0.3, 0.05, 0.01, 0.05, 0.01, 0.3), matching Study 2's pool profile.
- **F2 (100 tasks, 1 run each).**
  - Tasks are allocated to a primary type in proportion to max(π_D,k, φ), renormalised. The coverage floor φ ∈ {0, 0.05, 0.10}.
  - A task's primary type is present with probability 0.9. Other types appear at 0.5 × d.
  - **Trap enrichment e ∈ {1, 3}:** on a trap task's primary type, the flaw fires at min(1, e·r), because boundary traps over-sample trigger conditions.
  - Two pricing variants (implementation clarification written 2026-10-21, before any A′ run: these are two **alternative 100-task benchmark designs at the same cost**, not two readings of one benchmark):
    - **F2 pooled:** rates from all 100 tasks.
    - **F2 split:** 60 trap tasks are used for detection, and 40 deployment-representative tasks (opportunities = d, e = 1) for pricing. Detection uses all 100 tasks.
- **F3 (4 underwriters).** Underwriter u prices configuration c as clean_mean × v_c × B × ε_uc, where:
  - clean_mean is the deployment loss of a typical clean agent;
  - ε_uc ~ lognormal(0, 0.7) is individual error;
  - B ~ lognormal(0, 0.4) is a bias shared across underwriters;
  - **v_c** is what the card and transcripts show:
    - natural configurations: 2.5;
    - other configurations: 1;
    - in addition, each of the 10 sample transcripts (drawn from F1 tasks) showing a flawed event multiplies v_c by 1.5.

  The F3 interval is the min–max across underwriters, widened by 1.5×.
- **Experience period.** n_e ∈ {100, 200, 400} conversations per configuration, on tasks shared across configurations. Each conversation's opportunities follow d.
- **Realised loss** is the experience $/conversation measured by the same accounting.

**Forecast method:**
- **Rates.** For each forecaster and type, the rate estimate is shrunk towards a common mean:
  - prior: Beta(0.5, 0.5(1 − μ0)/μ0), where μ0 is that forecaster's pooled rate for the type across all 18 configurations;
  - posterior: updated with the configuration's events/opportunities.
- **Severity** uses the known E[severity] by type, because fares come from the database.
- **Point forecast** = Σ_k E[rate_k] × d_k × E[sev_k].
- **90% predictive interval:** posterior rate draws plus compound-Poisson experience noise at n_e.

**Cells and replications:**
- grid: λ ∈ {0.8, 0.5, 0.2} × φ ∈ {0, 0.05, 0.10} × e ∈ {1, 3} × r range ∈ {[0.05, 0.4], [0.02, 0.15]} × n_e ∈ {100, 200, 400};
- 300 replications per cell;
- seeds are fixed;
- Monte Carlo SE is reported.

**Performance measures (per cell):**
- detection rate by source and forecaster (F1, F2);
- false positives (clean 2 vs clean 1);
- per forecaster:
  - Spearman;
  - median |log error|;
  - coverage;
- the RQ3 gap;
- **P(H2 verdict)** = P(F2 non-designed detection ≥ 6/12);
- **P(H3 holds)** = P(both H3 conditions in a replication);
- **P(H4 holds)**;
- estimated cost.

**Predictions:**
- **A′-P1:** at λ = 0.8, F2 detects ≥ 80% of designed and external flaws at r ∈ [0.05, 0.4]. At λ = 0.2 with φ = 0, F2's non-designed detection falls below 50%. At φ = 0.10 it recovers to ≥ 60% at r ∈ [0.05, 0.4], but not at r ∈ [0.02, 0.15].
- **A′-P2:** F1 detects < 40% of flaws on bags, book or certificate in every cell.
- **A′-P3:** with e = 1, F2's median log error is ≤ ½ of F1's in most cells. With e = 3, pooled F2 overprices flawed configurations and H3 fails more often than with F2 split. F3 sits between F1 and F2.
- **A′-P4:** with 18 configurations, P(H3 holds) < 0.7 even where F2 is truly better, because Spearman over 18 points is noisy.

**Decision rules (fixed now):**
- **Detection** depends on benchmark size and firing rate, not on n_e. **H2 is decidable** in a cell if P(H2 verdict) is ≥ 0.8 or ≤ 0.2. The configuration count is held at 18 unless no cell is decidable.
- **n_e** for phase C′ is the smallest value at which P(H3 holds) in the reference cell (λ = 0.5, φ = 0.10, e = 1, r ∈ [0.05, 0.4]) is within 0.1 of its n_e = 400 value, and whose estimated cost fits the budget Ishaan sets.
- **φ:** the smallest coverage floor giving ≥ 60% non-designed detection at λ = 0.5 and r ∈ [0.05, 0.4] becomes **a design requirement for F2, communicated to Ishaan before he builds it.** It is a generic floor per action type, so it reveals nothing about the flaws.
- **Split rule:** if F2 split beats F2 pooled on P(H3 holds) at e = 3, the split (trap tasks for detection, representative tasks for pricing) becomes the frozen F2 pricing method.
- **Flaw-rate range:** the sealed catalogues use the narrowest range at which H2 is decidable at λ = 0.5. If neither range is decidable, they use [0.05, 0.4].
- **K1′** fires if no cell at λ = 0.5 makes either H2 or H3 decidable within an n_e of 400.

### A′ loop 1 results (2026-10-21; `results/study3/phaseA/sim_a.json`, tables in `results/study3/phaseA/tables.md`)
**Run:** 108 cells × 300 replications in 61 s, at $0 cost. Monte Carlo SE ≤ 0.03 on every rate below.

**Detection** (depends on benchmark and firing rate, not on n_e):
- At r ∈ [0.05, 0.4], F2 flags 0.72–0.76 of designed and 0.59–0.69 of non-designed flaws. F1 flags 0.54–0.59 and 0.40–0.48.
- At r ∈ [0.02, 0.15], every benchmark flags ≤ 0.35 of every source.
- False positives (clean 2 vs clean 1) are 0.00 everywhere.
- The shared-assumption gap (RQ3) ranges from +0.02 to +0.17. It grows as λ falls, but the effect is small.

**Single-target flaws by type:**
- F1 is almost blind to cabin, bags, book and certificate flaws (0.00–0.02).
- F2's coverage floor φ = 0.10 lifts cabin, bags and book only from 0.08–0.16 to 0.18–0.27. Ten tasks per type gives too few firings for the sign test.

**Pricing:**
- **F2 does not price better than F1.** At λ = 0.5, φ = 0.10, e = 1:
  - median |log error| is F1 0.39 and F2 pooled 0.38 at r ∈ [0.05, 0.4], n_e = 200;
  - Spearman is 0.83 vs 0.86.
- The reason is that flaws on F1's blind-spot types (bags $83, certificate $165) carry little deployment loss relative to cancel ($651) and statement ($408) flaws, which F1 already sees.
- **P(H3 holds) ≤ 0.01 in every one of the 108 cells.**
- Trap enrichment e = 3 raises F2 pooled's detection from 0.63 to 0.86, but doubles its median log error from 0.38 to 0.75 (a +0.70 log overprice on flawed configurations). F2 split keeps detection at 0.80 and its error at 0.47.
- **F3:** the underwriter model has no information on flaw magnitude, so it underprices flawed configurations by e^2.4. That is an artefact of my assumption, not evidence. A′ cannot inform H4.

**Predictions:**

| Prediction | Verdict |
|---|---|
| A′-P1 (λ = 0.8 → ≥ 80% detection; λ = 0.2, φ = 0 → < 50%) | **Not confirmed.** 0.75/0.68 and 0.59. The coverage floor barely moves the non-designed total |
| A′-P2 (F1 < 40% on bags, book and certificate) | **Confirmed** (0.00–0.02) |
| A′-P3 (F2 error ≤ ½ F1's; e = 3 pooled overprices; F3 in between) | **Not confirmed** / confirmed / not confirmed (an F3 model artefact) |
| A′-P4 (P(H3) < 0.7) | **Confirmed, but for a different reason:** under this world F2 is not truly better at pricing, and the +0.3 Spearman margin is unreachable when F1 already reaches 0.6–0.85 |

**Decision rules applied literally:**
- **H2** is "decidable" in every λ = 0.5 cell. P(H2) is 0.82–0.88 at r ∈ [0.05, 0.4] and 0.09–0.12 at r ∈ [0.02, 0.15]. So the narrowest-range rule picks [0.02, 0.15].
- **φ** = 0, because φ = 0 already gives 0.62 non-designed detection.
- **n_e** = 100 (P(H3) is 0 at every n_e).
- **The split rule does not trigger** (both P(H3) are 0).
- **K1′ does not fire** (H2 is decidable).

**These literal outcomes are degenerate:**
- the r ∈ [0.02, 0.15] verdict is decided by the firing rate, not by test design;
- the φ, n_e and split rules were keyed to an H3 probability that is 0 everywhere.

None of them is adopted. Loop 2 replaces them, as pre-registered below.

## A′ loop 2 (pre-registered 2026-10-21, after loop 1, before any loop-2 code)
**Aim:** find out when test design *can* matter, and make the decision rules informative. This is an adaptation of the simulation design. No real data exists yet, and no Study 3 primary outcome is frozen.

**Changes to the data-generating mechanism** (`src/trustcurve/study3/sim_a2.py`, which reuses `sim_a.py`):
1. **Severity profile S:**
   - S_A is loop 1's profile.
   - S_B is flat: every type has a median of $300, so blind-spot flaws cost as much per event as cancel flaws. This is a stress case, not a claim about airline fares.
2. **Runs per F2 task R ∈ {1, 3}.** F1 stays at 1 run per task (the Study 2 pipeline). R = 3 adds ≈ $43 at $0.012 per run.
3. **Grid:** λ ∈ {0.5, 0.2} × φ ∈ {0, 0.10} × e ∈ {1, 3} × r ∈ {[0.05, 0.4], [0.02, 0.15]} × n_e ∈ {100, 200, 400} × S ∈ {A, B} × R ∈ {1, 3}. That is 192 cells, with 300 replications each.

**New measures:**
- **H2 discrimination** = P(H2 verdict | F2) − P(H2 verdict | F1 used as the benchmark), using F1's own non-designed detection ≥ 6/12.
- **Paired detection power:** an exact one-sided McNemar test, F2 vs F1, over the 16 flawed configurations at α = 0.05.
- **Pricing comparisons:**
  - P(median |log error| of F2 < F1's);
  - the power of a one-sided paired sign test on per-configuration |log error| over 18 configurations at α = 0.05;
  - P(Spearman(F2) − Spearman(F1) ≥ 0.1).
- **Blind-spot loss share:** the share of true expected flaw loss on types where F1 has < 5 opportunities. P(H3) and the paired pricing power are reported for replications with a share ≥ 0.5.

**Decision rules (these replace loop 1's):**
- **Flaw-rate range:** the range with the larger H2 discrimination at λ = 0.5, S_A, R = 1, φ = 0.10.
- **R:** R = 3 is recommended if it raises the paired detection power by ≥ 0.15 at that range.
- **Split rule:** at e = 3, adopt F2 split if its median log error is lower than F2 pooled's by ≥ 0.1 and its non-designed detection is lower by ≤ 0.1.
- **φ:** the smallest φ at which single-target detection of cabin, bags and book is each ≥ 0.3 at the chosen range (and R). If none reaches it, report that per-type detection needs more opportunities, and recommend multi-opportunity tasks or a higher R.
- **n_e:** the smallest n_e at which the paired pricing-sign-test power is within 0.1 of its n_e = 400 value, in the cell chosen above under S_A.
- **H3 reformulation trigger:** if P(H3) is < 0.2 even in S_B cells with a blind-spot share ≥ 0.5, A′ recommends adding a decidable comparative H3b to the phase-B′ pre-registration. This happens before any data, and Ishaan decides. H3 itself stays as written.
- **K1′** fires only if H2 discrimination is < 0.3 and the paired pricing power is < 0.5 in every λ = 0.5 cell.

### A′ loop 2 results (2026-10-21; `results/study3/phaseA/sim_a2.json`, `tables2.md`, `decisions_loop2.json`)
**Run:** 192 cells × 300 replications in 107 s.

**Detection is limited by opportunity count, and runs per task is the lever:**
- At λ = 0.5, φ = 0.10, r ∈ [0.05, 0.4], moving F2 from R = 1 to R = 3 runs per task changes:
  - non-designed detection: 0.64 → 0.91;
  - designed detection: 0.72 → 0.94;
  - H2 discrimination against F1: +0.44 → +0.55;
  - paired McNemar power (F2 > F1): 0.24 → 0.86;
  - cost: +$43.
- At r ∈ [0.02, 0.15], R = 3 moves non-designed detection from 0.24 to 0.66 and discrimination from +0.07 to +0.83.
- F1, at 1 run per task, stays at 0.13–0.45.

**Per-type detection at R = 3:**
- with φ = 0.10: cabin, bags and book 0.68–0.72;
- with φ = 0 (2–4 tasks on the thinnest types): 0.37–0.60;
- F1: ≤ 0.04.

**Pricing:** F2 is only modestly better.
- At S_A, R = 3, n_e = 200: median |log error| is F1 0.40 vs F2 pooled 0.31, and Spearman 0.83 vs 0.90.
- P(F2's error < F1's) is 0.78, but the power of the paired per-configuration sign test is only **0.28**. Its maximum over all λ = 0.5 cells is 0.42.
- **P(H3) ≤ 0.07 in every cell**, including the flat-severity stress case S_B.
- The blind-spot loss share was 0.08–0.21 in every cell. Only 81 of 57,600 replications reached ≥ 0.5, so the conditional H3 analysis was not evaluable.

**Real-data anchor** (`scripts/study3/study2_loss_mix.py` → `study2_loss_mix.json`): in Study 2's 7,700 experience runs, **94.5% of realised commission dollars were wrongful cancellation refunds** (177 events). Certificates, bags and booking-on-another-account were 3.2%. So the real airline world is, if anything, more cancel-concentrated than S_A, and the pricing headroom from covering blind-spot *types* is small.

Study 2's pricing failure was instead **within** the cancel type:
- experience runs had 2.3% wrongful-cancellation events against 1.2% in underwriting;
- its planted faults sat on conditions the benchmark never set up.

The loop-1/2 simulation does not model that: within-type trigger conditions, and whether a designer anticipates them.

**Trap enrichment:**
- at e = 3, F2 pooled overprices by +0.68 to +0.71 log;
- F2 split stays at +0.05 to +0.12 with nearly the same detection.

**Loop-2 decision rules** (as pre-registered; `decisions_loop2.json`):

| Rule | Outcome |
|---|---|
| Flaw-rate range | **[0.05, 0.4]** (discrimination +0.44 vs +0.07 at R = 1). At R = 3 the narrower range discriminates more (+0.83 vs +0.55), but the rule is evaluated at R = 1 as written |
| R | **3** (McNemar power 0.24 → 0.86) |
| Split | **Adopted.** At e = 3, R = 3: error 0.71 → 0.36, detection loss 0.02 |
| φ | **0.** Cabin, bags and book each reach ≥ 0.3 at φ = 0, R = 3 (0.37–0.60). φ = 0.10 gives 0.68–0.72 |
| n_e | **200** (sign-test power 0.28 vs 0.29 at 400) |
| H3b trigger | **Fires by default.** No S_B cell had ≥ 20 replications with a blind share ≥ 0.5. The pre-registered condition was not evaluable, and the code treats "not evaluable" as firing. That is my interpretation: max P(H3) over all 192 cells is 0.07 |
| K1′ | **Does not fire** (max H2 discrimination 0.99) |

## A′ loop 3 (pre-registered 2026-10-21, after loop 2, before any loop-3 code)
**Aims:**
1. Model the mechanism that actually broke Study 2: flaws that fire only under a **within-type trigger condition**, which a benchmark covers only if its designer anticipated it. This gives the shared-assumption parameter λ real force.
2. Compare 18 vs 30 configurations at the same experience budget.
3. Measure the power of a candidate comparative H3b.

**Mechanism changes** (`src/trustcurve/study3/sim_a3.py`; everything else as in loop 2 at S_A):
- **Triggers.** Every flaw has a trigger condition with deployment prevalence q ~ U(0.15, 0.6) among opportunities of its type. It fires at min(1, r/q) on triggered opportunities, so its deployment rate per opportunity stays r.
- **Generic and representative tasks.** F1 tasks and F2's representative tasks carry the trigger at prevalence q.
- **F2 trap tasks on the flaw's type:**
  - if the designer *anticipated* the trigger, a trap task carries it with probability 0.9;
  - otherwise it carries it at 0.5·q, because the designer's traps crowd out other conditions.
- **P(anticipated):**
  - 0.8 for designed flaws;
  - 0.8·λ for non-designed flaws, with λ ∈ {0.8, 0.5, 0.2}.
- **No separate enrichment factor** (e = 1). Enrichment now arises from the anticipated triggers.
- **Fixed settings:** r ∈ [0.05, 0.4]; φ ∈ {0, 0.10}; R ∈ {1, 3}.
- **Size options, both with 3,600 experience conversations:**
  - 18 configurations × n_e = 200;
  - 30 configurations (2 clean + 7 per source) × n_e = 120.
- H2 uses ≥ 50% of the non-designed configurations (≥ 6 of 12 or ≥ 11 of 21).
- **F2 pricing** uses the adopted split (40 representative tasks × R). F2 pooled is reported alongside.
- **Grid:** λ (3) × φ (2) × R (2) × size (2) = 24 cells × 400 replications.

**Measures:** as in loop 2, plus:
- P(H1);
- P(H5: gap ≤ 0.25);
- the mean RQ3 gap by λ;
- H3b power = the one-sided paired sign test on per-configuration |log error| (F2 split vs F1), α = 0.05;
- cost:
  - 18 configurations: 18 × (90 + 100R) × $0.012 + 3,600 × $0.045;
  - 30 configurations: 30 × (90 + 100R) × $0.012 + 3,600 × $0.045.

**Predictions:**
- **A′-P5:** the RQ3 gap grows as λ falls, by ≥ 0.15 between λ = 0.8 and λ = 0.2 at R = 3.
- **A′-P6:** P(H5) falls below 0.5 at λ = 0.2.
- **A′-P7:** 30 configurations raise H3b power by ≥ 0.1 over 18, with H2 discrimination within 0.05.

**Decision rules:**
- **Size:** 30 configurations are recommended if A′-P7 holds. The ≈ $55 extra underwriting at R = 3 goes to Ishaan as a budget choice. Otherwise 18.
- **H5 informativeness:** if P(H5) differs by < 0.3 between λ = 0.8 and λ = 0.2, H5 cannot discriminate shared-assumption levels at this n. It is then reported descriptively, with its interval, rather than as a pass/fail test.
- **H3b:** if H3b power is ≥ 0.5 in the λ = 0.5 cell of the chosen size, A′ recommends H3b as a decidable comparative pricing test, added at B′ before any data. Otherwise A′ reports that **pricing superiority is not testable at an affordable n in this domain**, and Study 3's pricing questions (RQ2, RQ4) become estimation with intervals rather than tests.
- **This is the last A′ simulation loop** before the adapt memo and the fresh-context review.

### A′ loop 3 results (2026-10-21; `results/study3/phaseA/sim_a3.json`, `tables3.md`, `decisions_loop3.json`)
**Run:** 24 cells × 400 replications in 25 s.

**Detection** (F2 = the adopted split):
- **At R = 1, anticipation bites.** Non-designed flaws whose trigger the designer didn't anticipate are detected at 0.48–0.52, against 0.70–0.81 for anticipated ones.
  - The RQ3 gap grows as λ falls: +0.08–0.11 at λ = 0.8, +0.16–0.21 at λ = 0.5, +0.23–0.28 at λ = 0.2.
  - P(H5) falls from 0.80–0.86 to 0.42–0.59.
- **At R = 3, repetition largely substitutes for anticipation.** Unanticipated flaws are detected at 0.80–0.82, and the gap is only +0.04 to +0.12.
- F1 stays at 0.38–0.47 non-designed detection in every cell.
- McNemar power (F2 > F1) is 0.82–0.89 with 18 configurations and 0.96–0.99 with 30.

**Pricing** (median |log error|):
- **F2 split is no better than F1:** 0.39–0.47 vs 0.40–0.47.
- **F2 pooled is worse:** 0.48–0.62, because anticipated traps enrich triggers and inflate rates.
- H3b power (paired sign test) is ≤ 0.09 and P(H3) = 0.00 in every cell.
- Under this mechanism, F2's pricing advantage would have to come from being more *representative* of deployment than F1. The simulation makes both representative by construction, so it cannot test that.

**Predictions and decision rules:**

| Item | Outcome |
|---|---|
| A′-P5 (gap grows ≥ 0.15 from λ = 0.8 to 0.2 at R = 3) | **Not confirmed** (+0.04 → +0.10). It holds at R = 1 (+0.11 → +0.27, a post-hoc observation) |
| A′-P6 (P(H5) < 0.5 at λ = 0.2) | **Not confirmed at R = 3** (0.89). At R = 1 it is 0.42–0.59 |
| A′-P7 (30 configurations raise H3b power by ≥ 0.1) | **Not confirmed** (0.07 → 0.08). 30 configurations do raise McNemar power (0.85 → 0.99) and H2 discrimination (+0.60 → +0.75) |
| Size rule | **18 configurations** |
| H5 informativeness at R = 3 | **Not informative** (P(H5) 0.97 vs 0.89). Reported descriptively with its interval |
| H3b | **Not recommended as a test** (power 0.07). Pricing questions RQ2 and RQ4 become **estimation with intervals**, not pass/fail tests, unless the review or loop 4 shows otherwise |

### Corrections after review 10 (2026-10-21, post-hoc; see REVIEW.md review 10)
- **Loop-1 clarification relabelled.** The "implementation clarification written before any A′ run" first appears in the commit with the loop-1 results, so it is post-hoc.
- **Loop 3 (c) withdrawn.**
  - "Pricing superiority is not testable at an affordable n" holds only **if F1 is representative of deployment**, which the simulation imposed by construction.
  - A perfect forecaster's median |log error| is 0.27 at n_e = 200, so H3's ≤ 0.20 bar is unreachable for anyone. P(H3) ≈ 0 says nothing about test design.
  - With F1's triggers at 0.3·q, the reviewer found H3b power of 0.62.
  - **RQ2 is not converted to estimation.** Loop 4 decides.
  - **RQ4 is descriptive on its own grounds** (3–5 underwriters), not because of A′.
- **Loop 3 (a) and (b) restated.**
  - The F2-vs-F1 detection advantage mixes design with exposure (300 vs 90 task-runs).
  - The sign-test unit was runs, not the tasks S0 specifies.
  - Both are re-estimated in loop 4.
- **Loop 2 real-data anchor reworded.**
  - "94.5% cancellation refunds" describes **Study 2's own scenario mix, fault catalogue and ledger**, which had no statement peril. It is not a claim about "the real airline world".
  - The 2.3% vs 1.2% event rates compare different configuration sets and task pools.
  - The "pricing headroom is small" inference is dropped.
- **Unlabelled choices, now labelled.**
  - Implementation choices made in code: the rule cells e = 1 and n_e = 200; φ evaluated on 100 trap tasks.
  - **Post-hoc:** the loop-2 n_e rule used F2 pooled after the split was adopted. With the split, the literal rule gives n_e = 100.
  - **Post-hoc:** "not evaluable ⇒ the H3b trigger fires".
- **Mechanism and wording.**
  - Loop 3's deployment flaw rate is min(q, r), not r, for about 20% of flaws.
  - "Below ~0.15 undetectable" means r ∈ [0.02, 0.15] at R = 1.

## A′ loop 4 (pre-registered 2026-10-21, after review 10, before any loop-4 code; the final A′ loop)
**Aims:** settle what loops 1–3 left as artefacts.
1. Is pricing superiority testable when F1 or F2's representative tasks are unrepresentative, measured against a perfect-forecaster ceiling?
2. What does exposure-matched detection look like at the S0 per-task unit?
3. Choose n_e and the RQ1/RQ3 primary forms.

**Mechanism** (`src/trustcurve/study3/sim_a4.py`; as loop 3 unless stated):
- **Configurations:** 20, made up of **4 clean** (configuration 0 is the reference; the other 3 give the false-positive rate) and 4 per flaw source.
- **Fixed settings:** λ = 0.5, φ = 0.10, severity S_A.
- **Flaws:** trigger prevalence q ~ U(0.15, 0.6), and r is drawn as U(r_lo, min(r_hi, q)), so the deployment rate is exactly r.
- **Representativeness:** benchmark tasks carry a flaw's trigger at ρ·q (traps that anticipated it: 0.9).
  - F1 uses **ρ1 ∈ {0, 0.3, 0.6, 1}**.
  - F2's 40 representative tasks use **ρ2 ∈ {0.3, 0.6, 1, 1.5}**.
  - F2's unanticipated trap tasks stay at 0.5·q.
- **Forecasters:**

  | Forecaster | Definition |
  |---|---|
  | **O** | Perfect forecaster: true expected deployment loss. It shows the noise ceiling |
  | **F1₁** | 90 tasks × 1 run (Study 2-equivalent); the first run of F1₃ |
  | **F1₃** | 90 tasks × 3 runs |
  | **F2** | 60 trap + 40 representative tasks × 3 runs, split pricing (the 40 × 3 representative rows) |
  | F2p | Pooled pricing, reported only |

- **Sign-test unit (S0):** per task, summing events across runs, configuration vs reference. The run-level test is a sensitivity.
- **Grid:** ρ1 (4) × ρ2 (4) × r ∈ {[0.05, 0.4], [0.02, 0.15]} × n_e ∈ {100, 200, 400} = 96 cells, × 300 replications.

**Measures (per cell):**
- **Detection:**
  - non-designed and designed detection for F1₁, F1₃ and F2;
  - **exposure-matched McNemar power, F2 vs F1₃** (primary-candidate RQ1 test), and unmatched power vs F1₁;
  - false-positive rate over the 3 clean comparisons.
- **RQ3 as a difference-in-differences:** (F2 designed − non-designed) − (F1₃ designed − non-designed). Its mean, SD and 90% replication interval width.
- **Pricing, for each of O, F1₁, F1₃ and F2:**
  - median |log error|, Spearman, 90% coverage, and median log bias on flawed configurations;
  - P(H3) for F2 and for O (the ceiling);
  - **H3b power** (paired per-configuration |log error| sign test, F2 vs F1₃, one-sided α = 0.05), plus the same for O vs F1₃ (the ceiling).
- **Detection-vs-rate curve:** flag rate by r bin (0.02–0.05, 0.05–0.1, 0.1–0.2, 0.2–0.4) for F1₃ and F2, pooled over the ρ1 = 1 cells.
- **Cost:** the full line, which goes to Ishaan with prices rechecked before any spend.
  - underwriting: 20 × (90 + 100) × 3 × $0.012;
  - experience: 20 × n_e × $0.045;
  - statement judge: ≈ $0.004 per scored conversation, an estimate to be rechecked;
  - fidelity pilot + κ validation + planter: ≈ $25;
  - retries: + 10%.

**Calibration point (C2):** the ρ1 cell whose F1₁ median log bias on flawed configurations is closest to −0.7 (Study 2's underpricing order of magnitude), at ρ2 = 1.

**Predictions:**
- **A′-P8:** H3b power ≥ 0.5 at C2 with n_e = 200, and ≤ 0.15 at ρ1 = 1.
- **A′-P9:** matched McNemar power (F2 vs F1₃) ≤ 0.6 at r ∈ [0.05, 0.4], i.e. well below the unmatched 0.85.
- **A′-P10:** the difference-in-differences 90% width is > 0.4 at 4 designed configurations.

**Decision rules:**
- **n_e:** the smallest n_e ∈ {100, 200, 400} at which H3b power at C2 is ≥ 0.5 **and** ≥ 0.7 of the ceiling's power at the same n_e. If none qualifies, take n_e = 200, and RQ2 becomes estimation with intervals.
- **RQ2 form:**
  - **H3b is recommended as a pre-registered comparative pricing test** if it qualifies under the n_e rule. H3 stays as the plan states it and is reported as unreachable if O's P(H3) is < 0.2.
  - Otherwise RQ2 is estimation.
- **RQ1 form:**
  - if matched McNemar power is ≥ 0.6 at r ∈ [0.05, 0.4] and ρ1 = 1, it is recommended as the primary RQ1 test, with H2 reported alongside;
  - otherwise RQ1 is reported as detection-vs-rate curves with intervals, and H2 stays primary as the plan states.
  - Either way, the change goes to Ishaan.
- **RQ3:** reported as the difference-in-differences with its interval. If its 90% width is > 0.4, it is labelled as unable to distinguish "no shared-assumption effect" from a 20-point one.
- **K1′** fires only if neither the matched McNemar power nor H3b power at C2 reaches 0.5 in any n_e ≤ 400 cell.

### A′ loop 4 results (2026-10-21; `results/study3/phaseA/sim_a4.json`, `tables4.md`, `decisions_loop4.json`; pre-registration 9bbf26c)
**Run:** 96 cells × 300 replications in 79 s.

**Pricing against the perfect-forecaster ceiling (n_e = 200):**
- The perfect forecaster O has median |log error| **0.33** at r ∈ [0.05, 0.4] and **0.46** at [0.02, 0.15]. That is the experience-noise floor.
- **With F1 representative (ρ1 = 1):**
  - F1₃ has 0.43 and F2 has 0.47;
  - H3b power is ≤ 0.01 (ceiling 0.14–0.20).
  - There is no pricing advantage to detect.
- **At the Study-2-calibrated point C2 (ρ1 = 0.3; F1₁ bias −0.93 log at r ∈ [0.05, 0.4]):**
  - F2's error is less than half of F1₃'s (0.45 vs 1.01; Spearman 0.84 vs 0.72; coverage 0.88 vs 0.56);
  - but **H3b power is only 0.25** (ceiling 0.79). At n_e = 400 it is 0.34 (ceiling 0.86).
  - The bottleneck is the precision of F2's 40-task × 3-run pricing arm, not the size of the true difference.
- **With F1 fully unrepresentative (ρ1 = 0):** F1's Spearman is 0.05, close to Study 2's 0.006. Here P(H3) for F2 is 0.88–0.96 and H3b power 0.51–0.72.
  - **So the plan's H3 is reachable, but only in a world where the generic pool is as unrepresentative as Study 2's was.**
- **F2's representativeness cuts both ways.**
  - At ρ2 = 1.5 (over-represented triggers), F2 overprices by +0.40 log.
  - At ρ2 = 0.3, it underprices by −0.89 log, and its error is ≈ F1's.
  - **The representative arm must be written to match deployment. Over-trapping it destroys the advantage.**

**Detection** (exposure-matched, S0 per-task unit, ρ2 = 1):
- **With F1 representative (r ∈ [0.05, 0.4]):**
  - F2 detects 0.76 of non-designed flaws, against F1₃ 0.52 and F1₁ 0.39;
  - **matched McNemar power is 0.35** (run-level 0.39), against 0.68 unmatched.
- With F1 unrepresentative, matched power rises to 0.64 (ρ1 = 0.6), 0.92 (0.3) and 1.00 (0).
- **False positives** over 3 clean-vs-reference comparisons are ≤ 0.014.
- **Detection vs realised firing rate (ρ1 = 1):**

  | r | F2 | F1₃ |
  |---|---|---|
  | 0.02–0.05 | 0.25 | 0.15 |
  | 0.05–0.1 | 0.53 | 0.36 |
  | 0.1–0.2 | 0.72 | 0.52 |
  | 0.2–0.4 | 0.86 | 0.65 |

- **RQ3 difference-in-differences:**
  - its mean is +0.01 to +0.18;
  - its SD across replications is 0.20–0.31;
  - **its 90% width is 0.67–1.00.**
  - At 4 designed configurations, RQ3 cannot distinguish "no shared-assumption effect" from a large one.

**Cost** (full line, estimate; prices to be rechecked):

| n_e | Total incl. 10% retries | Underwriting | Experience | Judge | Pilot, κ validation, planter |
|---|---|---|---|---|---|
| 100 | $336 | | | | |
| 200 | **$444** | $137 | $180 | ≈ $62 | $25 |
| 400 | $659 | | | | |

**Predictions:**

| Prediction | Verdict |
|---|---|
| A′-P8 (H3b ≥ 0.5 at C2) | **Not confirmed** (0.25). The ≤ 0.15 part at ρ1 = 1 holds (0.01) |
| A′-P9 (matched McNemar ≤ 0.6) | **Confirmed** (0.35, vs 0.68 unmatched) |
| A′-P10 (DiD width > 0.4) | **Confirmed** (1.00) |

**Decision rules, applied literally:**

| Rule | Outcome |
|---|---|
| n_e | No n_e qualifies at either range. **n_e = 200** |
| RQ2 | **Estimation with intervals.** H3 and H3b are reported as secondary tests with their pre-computed power (H3b ≈ 0.25 at C2) |
| H3 | Not unreachable. P(H3) for O reaches 0.98–1.00 at ρ1 = 0 |
| RQ1 | Matched power is 0.35 < 0.6, so **H2 stays primary, as the plan states**. Detection-vs-rate curves and the matched McNemar test (power stated) are reported alongside |
| RQ3 | **Labelled uninformative** at 4 designed configurations (width 1.00). It is reported as an estimate, not a test |
| K1′ | **Does not fire.** Matched McNemar power reaches ≥ 0.5 when F1 is unrepresentative |

### A′ closing summary (2026-10-21; 4 loops, the maximum)
**What the planned design can decide:**
- **H1 and H2: yes.** P ≥ 0.94 at r ∈ [0.05, 0.4] *if* the world resembles the simulation. Real flaws that fire below about 5% per opportunity will mostly be missed by any benchmark.
- **Which kind of world the real study is in.** Whether F1 is representative shows up directly as F1's realised bias.

**What it cannot decide:**
- **Pricing superiority**, unless the generic pool turns out to be grossly unrepresentative (as in Study 2);
- **the shared-assumption gap** (RQ3);
- **underwriters vs benchmark** (RQ4, 3–5 people).

These are reported as estimates with intervals.

**Design carried into B′** (each item is still subject to Ishaan's decisions, below):
- **Configurations:** 20 (4 clean + 4 per source).
- **Runs:** **F1 and F2 both at 3 runs per task**, with F1₁ (first run) reported as the Study 2 equivalent.
- **F2:** 60 trap tasks (≥ 10% floor per money-moving type) + 40 deployment-representative tasks. **Pricing comes from the representative arm only.**
- **Experience:** n_e = 200.
- **Flaw rates:** 5–40% per opportunity where the source sets them (designed, mechanical); external and natural flaws at whatever rate they have.
- **Sign test:** per task.

**Untested lever (for Ishaan):** a larger representative pricing arm is the obvious way to raise H3b power, for example 100 representative tasks. A′ did not simulate it, and the loop budget is spent.

**Needs Ishaan before any paid B′ run:**
1. **The budget cap.** The full design is ≈ $444 (≈ $336 at n_e = 100), against ≈ $126 left under $500.
2. **Who builds F2**, and whether he accepts the F2 spec: ≥ 10% type floor, R = 3, a separate representative arm written to deployment frequencies, and possibly a larger representative arm.
3. **Whether to accept that RQ2 and RQ3 are estimation, not tests, at this size.** Raising them to tests would need ≫ 20 configurations.

## S1. Insurance-economics layer (secondary analysis; pre-registered 2026-10-21, before any B′ work and before any forecast freeze)
**Origin:** an amendment from Ishaan's parent session, relayed by a peer session on 2026-10-21. Its research base is the vault note "TrustCurve — Insurance Economics Research (2026-10-21)" (cited below as **IER §n**) and its source files.

**Questions:**
- (a) Would an insurer that prices from each forecaster make a profit?
- (b) Would the buyer pay?
- (c) What is the "premium for not being tested", measured against an outside-in rater that never looks at the agents?

**Scope:**
- $0. No paid runs.
- A pure computation over the frozen forecasts and the experience results.
- **No change to H1–H5, K1′–K4′ or any A′ decision.**

**Parameter tags:**
- **[V]:** IER's agent read the primary source.
- **[S]:** secondary or unconfirmed.
- **[D]:** derived arithmetic.
- **[A]:** an assumption made here.

The real-world costly-error frequency is **always a sweep, never asserted** (IER §5, §7: "No source: guess").

### E0. Outside-in forecasters (frozen with F1–F3)
- **F0, exposure-only.**
  - It uses HSB's filed cyber structure: premium = exposure base × hazard class × schedule modifier (IER §2 [V]; HSB Total Cyber manual 12/2015).
  - Every configuration is one "industry" with one per-conversation exposure unit, so **F0 is one flat rate per conversation**.
  - That rate is the book-wide mean of **F1₃'s** frozen point forecasts. F1₃ is the real design's primary F1 since A′ loop 4; the request said "F1". This is the outside-in pricer's information: the market average [A].
  - For rule (ii) below, F0's p75 is the book-wide mean of F1₃'s frozen p75s [A].
- **F0q, questionnaire.**
  - F0q = F0 × m_c / mean(m), so it is revenue-neutral against F0. This is the standard off-balance adjustment [A].
  - m_c is a schedule modifier built **only** from description-card fields an applicant would declare. Each factor sits within HSB's 0.9–1.1 per-criterion range, and the product is capped to 0.35–3.5 (IER §2 [V]).
  - The mapping, written now:

    | Card field | Modifier |
    |---|---|
    | Model tier | frontier 0.9; mid-tier 1.0; small or older 1.1 |
    | Money-moving tools present | yes 1.1; no 0.9 |
    | Human approval required for refunds or compensation | yes 0.9; no 1.1 |
    | A declared guardrail (policy-check step, refusal layer or harness) | yes 0.9; no 1.0 |

  - It uses no transcripts and no benchmark results.
  - Outdated policy documents and planted faults are not card-visible, by design.

### E1. Premiums per forecaster f ∈ {F0, F0q, F1₃, F1₁, F2, F3}
- **Pure premium** = the frozen point forecast in $ per conversation, total across the three perils. Per-peril premiums are also reported.
- **Permissible loss ratio (PLR):** **0.60** base, swept over 0.50–0.65 (IER §7; CAS 65% [V]; cyber 35–73% [S]).
  - It is consistent with acquisition 25% + admin 12% + about 5% profit, less 2.5% investment income [D]: 1 − 0.25 − 0.12 − 0.05 + 0.025 ≈ 0.60.
- **Rule (i), naive:** gross = point ÷ PLR.
- **Rule (ii), uncertainty-loaded:** gross = the 75th percentile of the forecaster's predictive distribution ÷ PLR.
  - **F1 and F2:** the 75th percentile must be stored at freeze. **This is a freeze requirement.**
  - **F3:** a lognormal fitted to the underwriters' median price and median 90% range.
  - **F0 and F0q:** as in E0.

### E2. The insurer's book per forecaster
- **Book:** each of the 20 configurations is one insured with **V conversations a year**: V = 10M base; sweep 1M and 30M (IER §5, §7 [D]).
- **Realised annual loss per insured** = the mean per-conversation loss of a bootstrap resample of its experience conversations, × V. B = 10,000 resamples [A]. The book loss distribution comes from the same bootstrap (insureds resampled independently).
- **Reported per forecaster:**
  - loss ratio (LR) = realised ÷ gross premium;
  - **combined ratio (CR) = LR + 37%**, the expense ratio: acquisition 25% + admin 12% (IER §7; Lloyd's 22.6% + 11.8% [V]);
  - underwriting profit;
  - investment income of 2.5% of premium.
- **Tail:**
  - the bootstrap 99.5% book loss;
  - **plus a correlated-flaw scenario** [A].
    - Take the largest realised excess loss per conversation (realised − the clean controls' mean) among the flawed configurations on the modal base model.
    - Apply it to **every** insured on that base model in the same year, × V.
    - This is the one-shared-flaw-hits-many case (IER §1: catastrophe bonds priced at 5–10× EL [V]).
- **Capital** = max(1.0 × gross premium, tail loss − expected loss), where the tail loss is the larger of the bootstrap 99.5% and the correlated-flaw scenario.
  - Capital ÷ premium 1.0 (IER §7; NAIC 0.77 [V]; Solvency II ≈ 0.4 + catastrophe [D]).
- **Return on capital** = (underwriting profit + investment income) ÷ capital, against a **10% cost of equity** (IER §7 [S]).
- **"Profitable" = CR ≤ 95% and RoC ≥ 10%** (Gen Re 95% target [V]).
- **Cross-subsidy map:** the loss ratio by configuration and forecaster.

### E3. Competition and adverse selection
- **Pairwise markets:** F0 vs F2, F0q vs F2, F1₃ vs F2, F3 vs F2.
- **Base:** each insured buys the cheaper rule-(ii) quote.
- **Sensitivity:** logit switching. P(buy from A) = 1 / (1 + exp(β·(log p_A − log p_B))), with **β = 5** [A].
- **Reported:** each insurer's **won-book** LR and CR.
- **Informed-buyer variant:** an insured whose realised loss is < 50% of its premium lapses with probability s ∈ {0, 0.3} [A]. This is selection like the telematics opt-in effect (IER §4 [V]).

### E4. Premium for not being tested
- **Per configuration:**
  - P(F0) − P(F2) and P(F0q) − P(F2), in $ and as a % of P(F0), under rules (i) and (ii).
- **Reported separately for:**
  - clean controls and low-risk configurations (realised loss below the book median): the overpayment by a safe company that isn't tested;
  - high-risk configurations: the outside-in insurer's underpricing, i.e. adverse selection.

### E5. Buyer side (a real-world assumption, labelled as such)
- **Premium ÷ saving:** premium per conversation ÷ (the saving per AI-resolved conversation × the resolution rate).
  - Saving: **$4** base, $3–6 (IER §5 [V/D]).
  - Resolution rate: **0.51** (Fin average [V]).
- **Premium ÷ expected loss.**
- Both are reported only at the E6 rescaled levels, never at raw Study 3 levels.

### E6. Levels caveat
**Study 3's $ levels come from trap-dense tasks.** So the headline is in **ratios**:
- LR and CR;
- relativities;
- premium ÷ expected loss;
- the F0 − F2 gap as a % of F0.

**Real-world reading:**
- Every configuration's realised and forecast loss is rescaled by one common factor k = f × E[severity] ÷ (the book-mean realised loss per conversation).
  - E[severity] is Study 3's own pooled event-severity mean.
  - **f** is a frequency sweep: **0.01%, 0.1%, 1%** costly errors per conversation (IER §5: "a guess, to sweep, not to assert").
- Ratios don't change under k. Only E5 and the capital floor do.

### Kill criteria for this layer (they end claims in this layer, not the study)
- **KE1:** no forecaster reaches CR ≤ 95% under rule (ii) at the base PLR → "not insurable on these forecasts at this maturity".
- **KE2:** F2's won-book LR in the F0-vs-F2 market is less than 10 LR points better than F0's → "testing adds little pricing value here". For comparison, Gallagher Re found that dropping the worst-scored 20% of cyber insureds cuts LR by up to 16.4% (IER §3 [V]).
- **KE3:** with the correlated-flaw scenario's capital, RoC < 10% for every forecaster → "the tail, not per-insured pricing, is the binding constraint".

### Case against (recorded before data)
1. **Cyber is an imperfect analogue.** AI errors are endogenous and correlated through shared models, so cyber history probably understates the tail (IER §3, §6).
2. **F0 vs F2 partly re-tests F1 vs F2 on levels,** because F0's flat rate is anchored on F1. The headline is therefore the cross-subsidy and selection *structure*, not levels.
3. **About 20 insureds is a toy book.** Each per-configuration LR is noisy.
4. **A′ already showed that F2's 40-task pricing arm is noisy** (loop 4: H3b power ≈ 0.25 at the Study-2-calibrated point). A cheapest-quote market rewards *underpricing* errors (the winner's curse). So E3 will penalise noise in every forecaster, F2 included. A KE2 "pass" or "fail" partly measures forecast precision, not only information.
5. **The correlated-flaw scenario is one constructed draw, not an estimated tail.**

### Implementation
- **Code:** `src/trustcurve/study3/econ.py`.
- **When:** written and given a known-truth smoke test on A′-style simulated forecasts during B′, **before** the forecast freeze. The freeze must store each forecaster's p75 and the description-card fields.
- **Locked decisions this layer must respect** (none conflicts):
  - 20 configurations;
  - F1 at R = 3;
  - F2 split pricing;
  - n_e = 200.
- **Noted for Ishaan:** F0 is anchored on F1₃, not F1₁.
