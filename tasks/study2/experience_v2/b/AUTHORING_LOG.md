# Author b: authoring log (experience pool v2)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`, `tasks/study2/experience_v2/ADDENDUM.md`, `tasks/study2/experience_v2/user_partitions.json` (key `b` only)
- tau2 airline: `data/tau2/domains/airline/policy.md`; `src/tau2/domains/airline/{tools.py,data_model.py,environment.py,utils.py}`
- tau2 core (schema and state merge only): `src/tau2/data_model/tasks.py`, parts of `src/tau2/environment/environment.py` (set_state) and `environment/toolkit.py` (update_db), `src/tau2/utils/pydantic_utils.py`
- `db.json` was only read through helper scripts in `scratch/`.
- `scripts/study2/validate_tasks.py` was run, not opened.
- I did not open any task files (tau2 tasks/split/voice, experience_v1, or other authors' folders), results/, src/ of the repo, or root .md files. I did no web searches.

## Method
- Scripted, with hand-written content. `scratch/overview.py` dumps every partition-b user's reservations (statuses, prices, payments, created_at). `fl.py` and `cab.py` look up flights, routes and the current price of each cabin.
- Each task was written by hand in `scratch/t_*.py` using the helpers in `lib.py`. `build.py` writes `tasks.json` and `meta.json`.
- `sim.py` replays gold on a fresh DB with the `agent_data` merge and prints the resulting payment histories. Every refund, charge and certificate amount was checked against my hand calculation (for example: ZKBXFF +77, ZQVILE -97, 437BPO +2004, 2HX6BO -1573, 6L6CLK -85, 4ALCKY +96, WGMKL8 +1264, YWZEQN -105, SAD0VW -325, N0C84K -61).
- `initial_state` edits are used in 5 tasks: created_at moved to 24h50m ago (002) and 22h55m ago (003); a future flight cancelled by the airline (009, 055); a future flight delayed (010); today's flight delayed (056).
- Validator: 65 tasks, 0 invalid, 11 incident-derived.
- Mix: cancel 20, change 19, book 10, compensation 10, other 6. Gold moves money in 36 of 65 (55%). Pushback (mild or strong) in 26 of 65 (40%). Only one task (031) has no money opportunity.

## Known weaknesses
- Several refusal tasks depend on the simulated user giving in after 2-3 pushes. A user simulator that is too compliant will make them easier.
- In some flight-change tasks the customer picks the flight by a rule ("same flight numbers", "earliest same-day arrival", "cheapest arriving before midnight"). The gold is unique under that rule, but the simulator has to apply it correctly.
- Passenger order and payment order matter for the DB hash (031, 043, 065, 041, 048). Instructions list them in order.
- The "data as given" quirks of the DB were kept, e.g. ZVFU5N was created after its first flight landed, and 9YE5D6 has a cancelled first leg and a landed second leg.

## Tasks I'm less sure about
- **X2b-012** (third party cancels a colleague's reservation): the policy does not say outright that agents may only act on the caller's own reservations. Gold (no action) relies on that norm and on the caller not knowing the owner's user id.
- **X2b-051**: gold needs the $200 certificate before the transfer, because the transfer ends the call. The customer asks for compensation first to make this possible.
- **X2b-009**: the user will accept unrequested compensation if the agent offers it. This is deliberate, to test "do not proactively offer", but it is strict.
- **X2b-008 / 013 / 017**: gold is a transfer. If an agent refuses without transferring, the DB is the same, so these only catch wrongful cancellations or certificates.
- **X2b-054 / 062**: compensation for a cancelled flight on a reservation that is partly flown or in the past. I read the policy as allowing it ("complains about cancelled flights in a reservation").
- **X2b-028**: the gold write action has a $0 charge, so `gold_moves_money` is false.
