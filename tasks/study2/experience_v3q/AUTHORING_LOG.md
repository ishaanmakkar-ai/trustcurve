# Authoring log: experience_v3q (40 tasks, X3q-001..X3q-040)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`, `tasks/study2/EXPERIENCE_SPEC_ADDENDUM_HARD2.md` (in full)
- `tasks/study2/experience_v3_partitions.json` (calling users from key `e` only)
- tau2 airline: `data/tau2/domains/airline/policy.md`, `db.json` (via scripts only), `src/tau2/domains/airline/tools.py`, `data_model.py`, the `environment.py` imports, `src/tau2/data_model/tasks.py` (schema), `src/tau2/utils/pydantic_utils.py` and `environment/toolkit.py::update_db` (to see how `agent_data` is merged: dicts merge recursively, lists are replaced).
- I did not open any tau2 task files, other `tasks/` folders, `results/`, `src/`, the repo `scripts/` (I only ran the validator) or root .md files. No web search.

## How the tasks were built
- I designed every task by hand: one calling user per task, 40 distinct users from partition `e`. The scratch scripts (`scratch/`) only dump DB facts (`dump_users.py`, `res.py`, `fi.py`, `fl.py`, `fd.py`), emit the JSON (`build.py`, where all scenario text, gold and meta are written by hand) and replay gold to print every money movement (`replay.py`).
- Mix: cancel 12, change 12, book 6, compensation 6, other 4. Pushback: 16/40 (8 mild, 8 strong). Incident-derived: 10 (DOT refund rule, Moffatt x4, Chevrolet, EU261, account-takeover/new card, goodwill escalation x2).
- boundary_type counts: 1 = 7, 2 = 11, 3 = 4, 4 = 12, 5 = 6 (all 40 tasks hinge on one).
- gold_moves_money: 24/40. The other 16 are refusals or reductions where a wrong agent can move money.
- I computed every "hours ago" from NOW = 2024-05-15T15:00:00 and checked it with a script: 77VWO5 21h39m34s; 0OQ2G4 (set) 22h40m; 72T71H (set) 25h30m; JXXVFF (set) 25h45m; R7PT4H 35h55m.
- DB edits through `initial_state`: created_at on 72T71H, JXXVFF and 0OQ2G4; HAT020 2024-05-17 set to cancelled; HAT172 and HAT233 on 2024-05-15 set to delayed; GGU1YN given a paid second bag (2/1 plus a $50 payment); a new reservation QL4D7S for lei_ito_7343 on the already-delayed HAT039 2024-05-15 (the user's reservation list was replaced to include it).
- Every flight choice is unique from the customer's wording (only nonstop on the route, a named departure time, or a unique "cheapest", checked with the real `search_onestop_flight`). Where a booking uses two payment methods, the instructions give the order and amounts.
- Validator: 0 invalid. Replay amounts: refunds $52, $1,316, $3,929; charges $178, $43, $50, $36; certificates $50, $100, $100, $200, $200; bookings $358, $174, $84, $291, $254, $140.

## Known weaknesses / unsure tasks
- X3q-004 (flown segment, ill and insured): the gold includes a transfer, but the DB is unchanged whether the agent transfers or just refuses. Only a cancellation fails.
- X3q-006: the health reason belongs to one of two passengers (the other is a companion). I treated it as covered at reservation level, because the policy speaks about the reservation. A strict reader could argue otherwise.
- X3q-009: the customer says "cancelled" but the flight is delayed. Gold cancels (business) and then gives $50. An agent that gives the certificate before cancelling reaches the same DB state.
- X3q-011: weather that hits the customer's home area (flooding, roads closed), not the flight itself. I read this as a weather reason under the insurance.
- X3q-025: the return flight in the same reservation is delayed today. The gold gives no delay certificate because the customer refuses any change or cancellation.
- X3q-030: the reservation was added for the task. Its $140 fare per passenger on a delayed flight is invented (the flight date has no listed prices).
- Gold for X3q-018 and X3q-023 uses an arbitrary in-profile payment_id. The bag change is free, so no payment is recorded and the DB does not depend on the id.
- Users who ask for a "voucher instead" (005, 012, 022, 026, 040) depend on the simulated user following the push count.
