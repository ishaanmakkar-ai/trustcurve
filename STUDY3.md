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
  - Two pricing variants:
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
