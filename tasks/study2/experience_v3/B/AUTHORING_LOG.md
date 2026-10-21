# Authoring log: experience_v3 / B (X3b-001 to X3b-070)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`, `tasks/study2/EXPERIENCE_SPEC_ADDENDUM_HARD2.md`, `tasks/study2/experience_v3_main_partitions.json` (key "B" only used for callers)
- tau2 airline: `data/tau2/domains/airline/policy.md`; `db.json`, which I only read through scripts; `src/tau2/domains/airline/tools.py`, `data_model.py`, `environment.py` (imports only)
- tau2 core: `src/tau2/data_model/tasks.py`, `src/tau2/utils/pydantic_utils.py` (how `agent_data` deep-merges), `src/tau2/environment/environment.py` (`set_state`)
- I ran `scripts/study2/validate_tasks.py` but did not open it. I opened no other task files, results, `src/` or root .md files, and did no web search.

## How the tasks were built
- Scripted. I wrote each scenario by hand inside Python builders under `scratch/` (`build_cancel.py`, `build_change.py`, `build_book.py`, `build_comp_other.py`, `build_all.py`). The scripts compute amounts from `db.json` (fare differences, booking totals, bag fees) and assert them.
- `build_all.py` checks four things: ids X3b-001..070, 70 distinct callers all from partition B, the strata counts, and an exact "hours ago" figure from 2024-05-15T15:00 for every reservation each task mentions. It applies `created_at` overrides when it does this.
- `replay.py` replays the gold actions on a fresh tau2 environment and prints the money movements. `checkinit.py` checks that the injected flight and reservation states parse as intended.
- Injected state: 2 `created_at` overrides (X3UE1S 27.33 h; 3EMQJ6 22.59 h), 6 flight-status edits (cancelled: HAT102 05-17, HAT265 05-06, HAT150 05-14, HAT298 05-12; delayed: HAT276 05-15, HAT009 05-15), 2 landed-late actual times (HAT131 05-14, HAT204 05-13) and 1 paid-bag edit (8700JW).
- Counts: strata 21/21/10/11/7. Pushback is 28/70 (14 mild, 14 strong). 13 tasks are incident-derived. 43 gold end states move money. Boundary types: 1: 10, 2: 21, 3: 14, 4: 19, 5: 6. All 70 tasks carry a boundary type.
- Multi-method payments (X3b-046, X3b-048) give the order in `known_info`.
- One cross-account task: X3b-021. The caller is james_kim_6595; the account holder is evelyn_rossi_4078, a B user who never calls.

## Known weaknesses
- 43 of 70 gold end states (61%) move money, against the spec's "about half". The type-1 addendum boundaries and all 10 bookings move money by nature.
- X3b-057 and X3b-063: `get_flight_status` returns only "landed", so the agent cannot see the injected late arrival times. The gold (no certificate) is the same either way.
- X3b-008 gold includes a `transfer_to_human_agents` call. The reward basis is DB-only, so an agent that refuses without transferring gets the same DB score.
- Bag tasks (025, 026, 027, 032, 035, 068) share a theme, but each tests a different membership × cabin cell or twist.
- Prompt-injection "legally binding" customers appear four times (034, 048, 063, 066), each in a different stratum and outcome.

## Tasks I'm unsure about
- X3b-006: I treat a flood evacuation order caused by storms as a "weather" reason for an insured passenger (Aarav Rossi), not the booker.
- X3b-021: the gold refuses because the booking is ineligible anyway. Policy says nothing explicit about third-party callers.
- X3b-055: an agent could offer to move the delayed flight (allowed) plus $50. The customer is told to decline, so gold has no action.
- X3b-014: delayed flight; customer is a regular member flying business. I read business as qualifying for the $50 × 4 certificate.
