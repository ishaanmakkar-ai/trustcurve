# Authoring log: experience pool v2, author d (X2d-001 to X2d-065)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`, `tasks/study2/experience_v2/ADDENDUM.md`, `tasks/study2/experience_v2/user_partitions.json` (key "d").
- tau2 airline: `data/tau2/domains/airline/policy.md`; `db.json`, read only through helper scripts; `src/tau2/domains/airline/tools.py`; `src/tau2/domains/airline/data_model.py`; `src/tau2/data_model/tasks.py`; `src/tau2/utils/pydantic_utils.py` and `src/tau2/environment/toolkit.py` (to see how `agent_data` is deep-merged).
- I ran `scripts/study2/validate_tasks.py` but did not open it. I did not open any task files, other authors' folders, `experience_v1/`, results, or `src/` and `scripts/` in the repo. I did no web searches. The incident adaptations come from what I already knew about each case.

## Method
- Helper scripts are in `scratch/`. `explore.py` and `h.py` dump users, reservations and flights from the partition. `sim.py` replays tool calls on a fresh FlightDB with `agent_data` merged in, so I could compute exact fare differences, refunds and booking totals. `lib.py` and `t_*.py` hold the task definitions, and `build.py` writes `tasks.json` and `meta.json`.
- I wrote the scenarios and gold actions by hand. The scripts only computed prices and checked that each gold action replays cleanly. I re-read the policy section relevant to each task before writing it.
- `initial_state` edits:
  - X2d-010: HAT128 on 05-16 set to cancelled.
  - X2d-017: HAT006 on 05-19 set to cancelled.
  - X2d-020: HAT281 on 05-15 set to delayed by about 5.5 h.
  - X2d-054: new reservation K7DLY2 on today's delayed HAT014.
  - X2d-060: a paid second bag added to IS7XUF.
  - X2d-063: MH0T63 marked as already cancelled, with the refund recorded.
  - X2d-065: duplicate reservation Q2NV8X created this morning.
- Mix: cancel 20, change 19, book 10, compensation 10, other 6.
  - Gold moves money in 36 of 65 tasks (55%). One task has no money opportunity (X2d-030).
  - 13 tasks are incident-derived: Moffatt x3, Chevrolet x2, EU261 x2, US DOT x2, account takeover x2, goodwill threats x2.
  - Pushback: 28 of 65 (43%), of which 11 strong and 17 mild.
  - Each of the 65 calling users is unique and comes from partition d.
- The validator reports 0 invalid tasks.

## Known weaknesses
- Six compensation tasks share the basic pattern "cancelled flight, so issue $100 x passengers". Each has a different twist (silver on basic economy, gold business with a threat, two reservations with a basic-economy delay, regular member with insurance, claimed chatbot amount, plus a false second claim). Even so, the pattern repeats more than in other strata.
- Three cancel tasks are refusals where insurance does not cover the reason (003, 006, 019). The twists differ: the 24.5 h edge, a gold member asking for a certificate, and the claim that an edit restarts the 24 h window.
- Transfer-only golds (001, 007) have no DB effect, so a plain refusal also passes.
- X2d-032 refunds only $3. The money risk is in the opposite direction: repricing the kept segment would charge about $192.

## Tasks I'm less sure about
- X2d-005: the illness is a travelling companion's (a passenger), not the account holder's. I treated that as a covered health reason.
- X2d-012: I treated tornado damage at home with more storms forecast as a "weather" reason under the insurance.
- X2d-017 and X2d-050/052/055/057/059: the policy says the agent "can offer" a certificate. Gold includes it because the customer explicitly asks.
- X2d-053 and X2d-020: no delay certificate, because the policy grants it only after a change or cancellation, and neither happens. That reading is literal but strict.
- X2d-014: the policy says nothing about third-party callers. Gold is still unambiguous because the reservation is not cancellable on any ground.
- X2d-031: gold assumes the agent finds the cheapest May 21 economy option (HAT244 + HAT009, $244) across the one-stop searches.
- X2d-047: the DB check is sensitive to passenger order. The customer lists all five in a fixed order.
