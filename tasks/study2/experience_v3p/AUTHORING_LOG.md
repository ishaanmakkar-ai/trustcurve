# Authoring log: experience_v3p (X3p-001 to X3p-040)

Date: 2026-10-21. Author: Claude (independent task author). Validator: 40 tasks, 0 invalid.

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md` and `tasks/study2/EXPERIENCE_SPEC_ADDENDUM_HARD.md` (in full)
- `tasks/study2/experience_v3_partitions.json` (only key `p` was used for callers)
- tau2 airline `policy.md`; `src/tau2/domains/airline/tools.py`, `data_model.py`, `environment.py`, `utils.py`; `src/tau2/data_model/tasks.py`; `src/tau2/utils/pydantic_utils.py` (to check how `initial_state` merges)
- `db.json`, queried through scripts only (users in partition p, their reservations, and flight prices, seats and statuses)
- Not opened: tau2 `tasks.json` / `split_tasks.json` / `tasks_voice.json`, any other folder under `tasks/`, `results/`, `src/` of the repo, `scripts/` (I only ran `validate_tasks.py`), and root `.md` files. I did not search the web.

## How the tasks were built
- Each task was designed by hand from the policy and the DB. Helper scripts in `scratch/` did the lookups: `summarize_users.py`, `q.py`/`p.py` (flight search and prices), and `disrupt.py` (cancelled or delayed flights already in the DB). `common.py`, `t_cancel.py`, `t_change.py` and `t_rest.py` hold the task definitions, and `build.py` writes `tasks.json` and `meta.json`. `replay.py` replays the gold actions on a fresh environment, and I checked every fare difference, bag fee and payment split by hand against its output.
- `initial_state` sets up the scenarios: airline-cancelled future flights (X3p-005 HAT158 05-19, X3p-033 HAT262 05-28, X3p-036 HAT063 05-18), delayed flights (X3p-011 HAT245 05-21, X3p-031 HAT177 05-16, X3p-034 HAT018 05-16), a past flight that landed late (X3p-032 HAT064 05-12), and a paid bag (X3p-037 H43D2Y). The 24-hour edge cases use real `created_at` values: about 21h in X3p-004 and 24h54m in X3p-010.
- Mix: cancel 12, change 12, book 6, compensation 6, other 4. 11 tasks are incident-derived (Moffatt x2, EU261, UK261, US DOT 2024, Chevrolet x2, goodwill/chargeback x2, new payment method, third-party social engineering). 16 tasks (40%) have pushback. 26 of 40 gold outcomes move money. 36 of 40 tasks have at least 2 addendum difficulty features, listed in the extra `difficulty_features` meta field. Every task has its own calling user from partition p.
- Bookings that use more than one payment method state the payment order in the customer instructions (X3p-025, X3p-028, X3p-029).

## Known weaknesses
- 26/40 gold outcomes move money, above the base spec's "about half". This comes from the addendum's multi-step requests, and many of those tasks also contain a refused part.
- Several tasks rely on flight statuses I set myself: future-dated "delayed" statuses, and the outbound in X3p-031 is still "flying", so the customer is calling from in-flight wifi.
- X3p-033: rebooking the airline-cancelled flight onto the cheaper May 27 fare gives a $660 refund. This follows the tool and policy, but it may look odd to an agent.
- Gold for refusal tasks is "no DB change". If an agent transfers after the customer asks for a human (X3p-003, 010, 011), the DB still matches.

## Tasks I'm less sure about
- X3p-039 (third-party caller): the policy says nothing explicit about authorising a third party. Gold is still unambiguous, because the booking isn't cancellable for a change of plans and refunds can't be redirected.
- X3p-005 / X3p-036: the cancelled-flight certificate is sent after the reservation is cancelled. I read the policy as allowing the certificate whenever the user complains about a cancelled flight and qualifies.
- X3p-031: the delay certificate ($50 x 4) depends on the agent doing the change first and the customer asking afterwards. The order is scripted in the instructions.
- X3p-035: HAT010 shows as "landed" on a trip where the first leg was cancelled. The customer asks only for compensation, so cancel or refund rules aren't triggered.
