# Research: how premiums are set, and how many observations you need

Research pass for the TrustCurve pilot (2026-10-21). `[U]` = unverified, `(d)` = derived by us from cited formulas. Sources are listed at the end and cited as [n].

## 1. How a premium is built
- **Fundamental insurance equation:** Premium = Losses + loss-adjustment expense + underwriting expenses + profit [1].
- **Pure premium (PP)** = Losses / Exposures = **Frequency × Severity** [1].
- **Loss-cost method (new lines with no existing rate):** R = (PP + F) / (1 − V − Q), where F is fixed expense per exposure, V is variable expense % and Q is profit and contingencies % [1, p.141]. The loss-ratio method adjusts an existing rate, so it can't price a brand-new cover.
- **Risk and capital load on top** [9]:
  - expected-value principle: (1+θ)E[S]
  - standard-deviation principle: E[S] + θσ
  - cost of capital: E[S] + r·C, with C = VaR or TVaR − E[S]. Solvency II uses r = 6%; the UK uses 4% [10]. For a thin, correlated line this load can exceed the expense load.
- **Exposure base:** it must be proportional to expected loss, practical, and consistent with precedent [1, p.49]. For agents the candidates are per conversation, per transaction, or per $ of refund/payment authority. **One benchmark run counts as one exposure only if it matches a real-world unit in expected loss.**

## 2. How many observations: credibility
- **Primary-text verification (2026-10-21, done directly, not delegated):**
  - Werner & Modlin, *Basic Ratemaking* (CAS), Ch. 12, book pp. 218–220 (PDF pp. 230–232). Full standard E(Y) = (z/k)² = (1.645/0.05)² = 1,082. Square-root rule Z = √(Y/E(Y)), with their worked example 100 claims → Z = 0.30 → 0.30·$200 + 0.70·$300 = $270. Stated assumptions: homogeneous exposures, Poisson claims, no severity variation. The appendix exhibits use the 1,082 standard in practice (e.g. 683 claims → Z = 79.5%).
  - *Loss Data Analytics* ch. 9: eq. 9.4 (frequency standard with σ²/μ; binomial 1−q in Ex. 9.2.3), eq. 9.8 (Bühlmann Z = n/(n+K), K = EPV/VHM), eq. 9.10 (Bühlmann–Straub Z = m/(m+K)).
- **Limited-fluctuation full standard:** n_F = (z/k)². At P = 90% (z = 1.645) and k = 5%, n_F = **1,082 claims** (verified against the CAS text [1, Table 12.1; 5]).
  - Other points on the same table: k = 10% → 271 claims; 95%/5% → 1,537; 99%/5% → 2,654 (z = 2.576).
  - Assumptions: Poisson claim counts, homogeneous exposures. The count is of *claims*, not exposures.
- **General frequency:** n_F = (z/k)²·σ²/μ. σ²/μ is **1 − q for binomial** [2, eq. 9.4].
- **Pure premium including severity:** (z/k)²·[σ²/μ + CV_X²] [1, p.219; 2, eq. 9.5]. **Severity variance usually dominates.**
- **Partial credibility:** Z = min(1, √(n/n_F)); the estimate is Z·X̄ + (1−Z)·M, where M is the complement (manual rate) [1; 2].
- **Bühlmann:** Z = n/(n+K), with K = EPV/VHM (within-risk noise ÷ between-risk signal). Bühlmann–Straub generalises to unequal exposure. For a beta-binomial model it equals the Bayesian posterior mean [2, §9.5].
- **The unit:** the standard applies **per rating cell**, i.e. one homogeneous risk being priced. You can't pool unrelated risks to reach 1,082 [1]. Here a cell is **one configuration: model + version × scaffold/prompt × domain × tool permissions.**

## 3. Adapting it to agent evals
- **Each run is a Bernoulli trial** (loss event with probability q), not a Poisson exposure period (d):
  - failures needed = 1,082·(1−q); runs needed = 1,082·(1−q)/q
  - with severity: [(1−q) + CV_X²]·(z/k)²/q runs
- **Clustering (the big one):** repeating a task gives correlated runs.
  - Design effect DEFF = 1 + (m−1)ρ, where m is repeats per task and ρ the intra-class correlation (ICC) [13]. Effective n = N·m/DEFF.
  - As m grows, effective n tends to **N/ρ** (d). With **50 airline tasks** [16]:
    - ρ = 0.3: ceiling ≈ 167
    - ρ = 0.5: ceiling ≈ 100
  - **Unit correction (review 1, #3):** the ceiling N/ρ is in effective **runs**. Effective **loss events** ≈ q·N/ρ. Example: q = 0.4, ρ = 0.3 gives about 67 effective failures, against 1,082·(1−q) = 649 needed for frequency alone. **Repeats alone cannot reach the full standard.** Compare runs needed, 1,082·(1−q+CV²)/q, with N/ρ, and use ρ of the *loss-event* indicator.
  - Evidence that ρ is large (indirect: τ-bench retail on another model): in τ-bench, pass^1 0.46 vs pass^4 0.225 for one model, against 0.045 if trials were independent [17, secondary] (d). Clustered errors inflated standard errors up to ~3× on public evals [11].
- **Link between ICC and Bühlmann:** for a beta-binomial model, ρ = 1/(α+β+1), so K = (1−ρ)/ρ (d). The pilot's ICC estimate both sizes the main run and sets the credibility weights.
- **Workflow mix:** post-stratify, E[L] = Σ_h w_h·q_h·μ_h, using the insured's real mix w_h. Unequal weights add a Kish design effect ≈ 1 + CV_w² [13]. Credibility then has to hold per heavily weighted stratum.
- **Is 1,082 right?** It's a convention.
  - k = 10% (271 claims) or even 20% (68) is defensible for a new line if: residual uncertainty is priced in the risk load, the result is credibility-blended with a complement, and limits/deductibles cap the tail [1].
  - **Realistic target: ±10–20% on frequency for one configuration, with severity capped.** Anything tighter needs hundreds of distinct tasks.

## 4. Special cases
- **Zero failures:** the 95% upper bound is ≈ 3/n (rule of three) [14]. Exact Clopper–Pearson: one-sided 1 − 0.05^(1/n); two-sided ≈ 3.69/n. Use effective n, not raw n.
- **Intervals:** use **Wilson** or Jeffreys, not Wald, at small n or near 0 or 1 [15]. Don't use CLT intervals below a few hundred items [12].
- **Heavy-tailed severity:**
  - Lognormal σ = 1.5 gives CV² = 8.5, which inflates the standard about 9.5× (d).
  - A Pareto tail with α ≤ 2 has infinite variance, so no classical standard exists.
  - Price a basic limit with the limited expected value E[X∧B], plus increased-limit factors [7].
  - **τ² severities are bounded** by ticket and compensation values, so they're basic-limit severities only. Legal and regulatory tails are absent.
- **Rare catastrophes:** not observable in a pilot. Use scenarios plus a catastrophe/capital load.
- **Accumulation:** with N insureds at pairwise correlation ρ, Var = Nσ²[1 + (N−1)ρ] (d). More than 80% of deployments sit on three model providers [24, secondary] `[U]`. This is a portfolio property that a single insured's eval can't measure.
- **Model or version drift = a new rating cell.** Old data is at most a complement, on-levelled via paired evals [11]. Contracts need re-test triggers.

## 5. How new lines get priced without loss history
- Early cyber insurance used questionnaires, a few objective factors, external base rates and judgement [18 `[U]` detail; 19; 20].
- Parametric covers price the trigger probability; Munich Re's aiSure prices performance KPIs [21; 26].
- **Toolkit:** expert judgement, scenario and Monte Carlo models, analogous lines, credibility blending with a manual rate, and conservative structure (limits, deductibles, sublimits, exclusions).
- **Evidence an underwriter would plausibly accept** `[U]`:
  - an independent, reproducible protocol
  - frequency with honest clustered intervals
  - a $ severity distribution mapped to the policy's loss definition
  - representativeness of the insured's workflow
  - version control and re-tests
  - controls in place

## 6. Commercial framing
**Ishaan's aims:**
- found an AI-agent insurance company
- EF / BlueDot funding through Fulcrum
- he's an ex-YC founder
- he's based in London, a short trip from Lloyd's, the world's specialist-insurance market

**Who would buy this evidence:**
- **MGAs and Lloyd's coverholders** writing affirmative AI cover, such as Armilla with Chaucer [22]
- **carriers and reinsurers**, such as Munich Re [21]
- **certifiers that also insure**, such as AIUC [23]
- **enterprises** doing vendor due diligence
- **agent builders** backing performance warranties

**Decisions it changes:** accept or decline; deductible and attachment; per-claim and aggregate limits; rate; exclusions and sublimits; warranties (e.g. human review above $X); re-test conditions.

**What they'd pay:** no public pricing found `[U]`. Treat willingness to pay as a hypothesis for the underwriter calls.

**The wedge for TrustCurve:** the hard part isn't scanning or testing. It's turning tests into **honest, clustered, credibility-weighted frequency × severity per rating cell**, and saying plainly how many distinct tasks that needs. That is exactly the gap where underwriters say evidence is missing.

## 7. Implications for the pilot
See `PILOT_PLAN.md`. In short, measure:
- pass/fail **and** a separate loss-event flag (failure with nonzero $)
- signed $ severity
- task-level clustering (ICC, or EPV/VHM)
- severity CV and tail shape
- cost per run
- stratum labels
- a configuration fingerprint

## Sources
1. Werner & Modlin, *Basic Ratemaking*, 5th ed., CAS (2016). https://casact.org/library/studynotes/Werner_Modlin_Ratemaking.pdf
2. Frees et al., *Loss Data Analytics*, ch. 9. https://openacttexts.github.io/Loss-Data-Analytics/ChapCredibility.html
3. Mahler & Dean, "Credibility", *Foundations of Casualty Actuarial Science* (bibliographic only).
4. Herzog, *Introduction to Credibility Theory*, ACTEX (bibliographic only).
5. CAS RPM 2012 handout. https://casact.org/sites/default/files/presentation/rpm_2012_handouts_session_4767_presentation_973_0.pdf
6. Mahler, "An Actuarial Note on Credibility Parameters". https://casact.org/abstract/actuarial-note-credibility-parameters
7. Palmer, "Increased Limits Ratemaking", CAS (2006). https://www.casact.org/library/studynotes/palmer.pdf
8. Klugman, Panjer & Willmot, *Loss Models* (bibliographic only).
9. Kaas et al., *Modern Actuarial Risk Theory*. https://doi.org/10.1007/b109818
10. Solvency II Delegated Reg. 2015/35 Art. 39 (https://www.eiopa.europa.eu/rulebook/solvency-ii/article-2452_mt); UK SI 2023/1346 (https://www.legislation.gov.uk/uksi/2023/1346/regulation/2/made)
11. Miller, "Adding Error Bars to Evals" (2024). https://arxiv.org/abs/2411.00640
12. Bowyer et al., ICML 2025. https://arxiv.org/abs/2503.01747
13. Kish design effect: https://www150.statcan.gc.ca/n1/pub/12-001-x/1999001/article/4718-eng.pdf
14. Hanley & Lippman-Hand, JAMA (1983). https://jamanetwork.com/journals/jama/article-abstract/389714
15. Brown, Cai & DasGupta, *Statistical Science* (2001). https://projecteuclid.org/euclid.ss/1009213286
16. Barres et al., τ²-Bench. https://arxiv.org/abs/2506.07982
17. Yao et al., τ-bench. https://arxiv.org/abs/2406.12045
18. Romanosky et al., cyber insurance policies (SSRN 2929137).
19. CAS *Actuarial Review*, "Cyber Insurance: The Actuarial Conundrum". https://ar.casact.org/?p=1946
20. Awiszus et al. (2022). https://arxiv.org/abs/2209.07415
21. Munich Re aiSure. https://www.munichre.com/en/solutions/for-industry-clients/insure-ai.html
22. Armilla × Chaucer (2025). https://www.armilla.ai/resources/armilla-launches-affirmative-ai-liability-insurance-with-lloyds-underwriter-chaucer
23. AIUC. https://www.aiuc.com
24. AIUC, "Underwriting the Agent Economy" (2026), via summary. https://actuary.info/insights/ai-agent-provider-concentration-accumulation-risk-insurers-2026
25. TechCrunch (23 Nov 2025). https://techcrunch.com/2025/11/23/ai-is-too-risky-to-insure-say-people-whose-job-is-insuring-risk/
26. hyperexponential, parametric pricing. https://www.hyperexponential.com/lob-pricing-factors/parametric
