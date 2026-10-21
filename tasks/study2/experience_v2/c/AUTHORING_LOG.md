# Authoring log: experience pool v2, author c (X2c-001 to X2c-065)

## Files read
- `tasks/study2/EXPERIENCE_SPEC.md`, `tasks/study2/experience_v2/ADDENDUM.md`, `tasks/study2/experience_v2/user_partitions.json` (key "c"; I also used the key list to pick third-party users who are in no partition)
- tau2 airline `policy.md`; `src/tau2/domains/airline/tools.py`, `data_model.py`, `environment.py`; `src/tau2/data_model/tasks.py`; `src/tau2/utils/pydantic_utils.py` and `environment/toolkit.py` (`update_db`), read to understand how `agent_data` deep-merges
- `db.json`, read only through helper scripts in `scratch/`
- `scripts/study2/validate_tasks.py` was run, not read

I did not open any task files (the tau2 task, split or voice files, `experience_v1/`, or other authors' folders), `results/`, the repo's `src/`, or root .md files. No web searches and no LLM API calls.

## Method
- `scratch/dump.py` summarises every partition user's membership, payment methods and reservations, with the live status of each flight. `scratch/find.py` lists disrupted reservations. `scratch/s.py`, `q.py` and `q2.py` search flights and print reservations.
- I designed each task by hand against the policy. The task text is in `scratch/t_cancel.py`, `t_change.py`, `t_book.py`, `t_comp.py` and `t_other.py`.
- `scratch/build.py` replays the gold actions on a fresh environment (with `agent_data` applied) and prints the payment and certificate effects so fare differences can be checked. It derives `gold_moves_money` from the database diff, then writes `tasks.json` and `meta.json`.
- `agent_data` edits:
  - X2c-003: `created_at` moved to 25 h ago.
  - X2c-006: HAT083 on 05-25 set to cancelled.
  - X2c-052: HAT262 on 05-12 set to cancelled.
  - X2c-054: HAT260 on 05-15 set to landed.
  - X2c-058: HAT181 on 05-15 set to delayed.
- Validator result: 65 tasks, 0 invalid. 14 tasks are incident-derived. Gold moves money in 36 of 65 (55%). 27 of 65 customers (42%) push back.

## Known weaknesses
- The bag-addition tasks (024, 025, 037, 062, 063) have a similar shape. Each tests a different allowance tier or payment twist.
- Several refusal tasks rely on the simulated customer following a "decline after refusal" script. A weak simulator may drift.
- Gold passenger order in 028 and 064 must match what the agent sends. 028 keeps the original order.
- 029 gives a large refund ($993) because the kept segment stays at its original price, which is how the tool prices it. Reviewers may find this surprising, but it is how the tool behaves under this policy.

## Tasks I'm unsure about
- X2c-057: gold expects the certificate first and then a transfer for the refund of the partly flown trip. An agent that transfers before compensating fails. The customer is told to ask for compensation first.
- X2c-053: delay compensation after changing a friend's flight. The certificate goes to the booking user (the caller), not the passenger.
- X2c-055: delay plus insurance. An agent could argue the delay is "weather", but the customer says it is not.
- X2c-012: authority to act for a third party is not addressed by the policy. The gold (no action) is unaffected because the booking is ineligible either way.
- X2c-054: depends on the edited landed status of the first leg.
