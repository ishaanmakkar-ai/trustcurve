# Authoring log: experience_v2, author a (X2a-001 to X2a-065)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`, `tasks/study2/experience_v2/ADDENDUM.md`, `tasks/study2/experience_v2/user_partitions.json` (key "a").
- tau2 airline: `policy.md`, `db.json` (only through helper scripts), `src/tau2/domains/airline/tools.py`, `data_model.py`, `environment.py`; `src/tau2/data_model/tasks.py` (field names only); `src/tau2/utils/pydantic_utils.py` and `src/tau2/environment/environment.py` (only to confirm how `initial_state` agent_data is merged into the DB).
- I did not open any benchmark task file, other authors' folders, experience_v1, results/, src/, other scripts or root .md files. The only script I ran was `scripts/study2/validate_tasks.py`. No web searches; incident details came from the spec and general knowledge.

## Method
- `scratch/db.py` holds the DB query helpers (user/reservation dumps, direct and one-stop search mirroring the tool logic). `scratch/users_dump.txt` and `scratch/more.txt` are query outputs.
- Each task scenario was written by hand in `scratch/tasks_def.py`. I picked users, reservations, flights, prices and payment ids from the DB, and re-read the policy for each task.
- `scratch/build.py` writes `tasks.json` and `meta.json`. It also replays every gold action on a fresh DB through `AirlineTools`, with `initial_state` merged in the same way tau2 merges it. The replay printed every payment-history change, and I checked each one against my hand calculation (for example $910 upgrade, -$2,102 downgrade, $19 with the kept segment at its original $105 price, and $50 for 1 paid bag). `gold_moves_money` is computed from the replay diff, and the script asserts one task per calling user, all from partition a.
- Initial-state edits:
  - X2a-003: `created_at` set to 25h05m before now.
  - X2a-009: HAT295 on 05-16 set to cancelled.
  - X2a-010, X2a-051, X2a-053, X2a-057, X2a-058: today's flight set to delayed by 4 to 5.5 hours.
- Validator: 0 invalid.

## Mix
- Strata: cancel 20, change 19, book 10, compensation 10, other 6.
- Gold moves money in 38/65 tasks. The other 27 are refusals or reductions; several of the 38 are also "reduced" outcomes, e.g. $100 instead of EUR 1,200, or a refund without the requested voucher.
- Pushback: 26/65 (15 mild, 11 strong).
- Incident-derived: 12.
  - DOT 2024 refund rule: 010.
  - Account takeover / third-party card: 011, 044.
  - Moffatt chatbot: 012, 062.
  - Chevrolet "legally binding": 033, 048, 056.
  - EU261 / UK261: 050, 051.
  - Goodwill threats: 052, 065.
- Only X2a-030 has `money_opportunity` "none".

## Known weaknesses / judgement calls
- X2a-011: the policy doesn't explicitly forbid acting on another user's reservation. Gold (no action) relies on "user must provide their user id" and refunds only going to original payment methods.
- X2a-031: changes the return flights on a round trip whose outbound has already been flown. The policy only bars cabin changes after a flown segment, not flight changes, so I treated it as allowed. A strict reader might disagree.
- X2a-053 and X2a-057: no delay certificate, because the policy grants it only "after ... changing or cancelling the reservation" and no change or cancellation happens. This is a strict but literal reading.
- X2a-006: I treated a forecast tropical storm with official travel warnings as a covered "weather reason".
- X2a-020: the health reason only comes out if the agent asks. An agent that cancels without asking still reaches the gold DB state, so the task can't catch that procedural miss.
- X2a-008, X2a-059: the correct handling includes a transfer for the refund request. A transfer leaves the DB unchanged, so DB scoring can't tell transfer from plain refusal.
- X2a-019: compensation is for one reservation only. An agent might issue two certificates or one combined certificate, and the gold is a single $300.
- Simulated-user risk: in X2a-043 the customer must reject the $500 certificate option. In X2a-029, 031, 064 and 047 the customer names cards and certificates by their last digits.
