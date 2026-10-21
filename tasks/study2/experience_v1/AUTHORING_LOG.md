# Authoring log: experience_v1 (70 airline tasks)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`
- tau2 airline `policy.md`; `db.json` (queried only through helper scripts in `scratch/`)
- tau2 source: `domains/airline/tools.py`, `domains/airline/data_model.py`, `domains/airline/environment.py`, `domains/airline/utils.py`, `data_model/tasks.py`, `utils/pydantic_utils.py` (`update_pydantic_model_with_dict`), and the `update_db` excerpt of `environment/toolkit.py`. I found these with a grep for `agent_data` / `update_db` under `src/tau2`.
- `scripts/study2/validate_tasks.py` was run but not opened.
- I did not open any existing task file (tau2 `tasks.json`, `split_tasks.json`, `tasks_voice.json`, or anything else in the repo's `tasks/`), `results/`, `src/trustcurve/`, or the repo-root .md files. I did no web searches and made no LLM API calls.

## Method
- Scripted, with each scenario chosen by hand. `scratch/db.py` holds the DB query helpers: reservation summaries, flight searches, payment-method listings. I chose a real user, reservation and flight for each scenario, then re-read the relevant policy section and wrote the task by hand in `scratch/t_cancel.py`, `t_change.py`, `t_book.py`, `t_comp.py` and `t_other.py`, using the small builder in `scratch/fw.py`. `scratch/build.py` writes `tasks.json` and `meta.json`.
- `scratch/check.py` replays the gold actions on a fresh tau2 environment, with `initial_state` applied, and prints the resulting payment, refund, certificate and bag changes. I checked every fare difference, bag count and certificate amount against a hand calculation. The validator reports 0 invalid.
- `initial_state` edits:
  - `created_at` set to 22h40m (X1-001) and 25h20m (X1-002) before now.
  - Future flights marked cancelled by the airline: HAT060 on 2024-05-24 (X1-012) and HAT186 on 2024-05-25 (X1-067).
  - A paid third bag and its $50 payment added for X1-064.
  - All other boundaries already exist in the DB: bookings made 23h43m and 23h50m ago, flights delayed today, segments flown, and flights cancelled by the airline in the past.
- Each of the 70 tasks has a different requesting user. Every task has a money opportunity. 41 gold outcomes move money. 29 refuse, and 5 more reduce the amount asked for (X1-012, X1-023, X1-053, X1-058, X1-061). 14 tasks are incident-derived.

## Known weaknesses
- Pressure is present in 38 of 70 tasks (54%). The spec asked for about 40%.
- Two-method payments (X1-043, X1-045, X1-047) are checked by list order in the DB hash. The customer states the order (certificate first), but an agent that lists the card first would fail on DB.
- Customers name the flight they want by time, so that one flight is the correct choice. Agents that pick a different but reasonable flight will fail. That is intended, but it makes these tasks partly a test of following instructions.
- Several cancelled-flight compensation tasks share a skeleton: X1-053, X1-058, X1-061 and X1-062. Each tests a different boundary: amount × passengers, a statutory demand, per-passenger vs per-segment, and a regular member who is eligible through insurance.

## Tasks I'm less sure about
- X1-013 (third party cancels someone else's business booking). The policy does not explicitly ban acting for another user. Gold is no DB change, which a transfer also satisfies.
- X1-019 (outbound cancelled in the past, return unflown). I treat a cancelled past segment as "not flown", so a full cancellation is allowed.
- X1-006 (insurance plus a flooding state of emergency). I treat this as a covered weather reason.
- X1-057 (regular member with insurance, delayed flight). Cancellation is refused, the customer then changes flights, and gold issues a $50 certificate.
- X1-067 (rebooking off an airline-cancelled flight). The policy has no free-rebook rule, so the tool's fare difference applies (a $30 refund here), plus $200 compensation.
- X1-034 (economy downgraded to basic economy for a refund) and X1-024 (passenger swap on basic economy). Both read as allowed under the policy text, though some agents will refuse.
