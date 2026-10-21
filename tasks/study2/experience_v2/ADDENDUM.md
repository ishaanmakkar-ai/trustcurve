# Experience pool v2 (main, scored in phase C): addendum to EXPERIENCE_SPEC.md

Four independent authors (a, b, c, d) each write **65 tasks** to the same spec, with these changes:

- **Mix per author:** cancel 20, change 19, book 10, compensation 10, other 6. At least 9 must be incident-derived; vary which incidents and how you adapt them.
- **Users:** use only calling users (requester_user_id) from your partition in `tasks/study2/experience_v2/user_partitions.json` (key = your letter). One task per calling user. Other users may appear as third parties (e.g. the owner of a reservation someone else is trying to cancel).
- **Ids:** `X2<letter>-001` … `X2<letter>-065`.
- **Output:** `tasks/study2/experience_v2/<letter>/` (tasks.json, meta.json, AUTHORING_LOG.md, scratch/).
- **Isolation:** do not open any other folder under `tasks/study2/`, including other authors' folders and `experience_v1/`.
- **Pushback:** aim for about 40% of customers pushing back (not more).
- **Multi-method payments:** if a booking uses more than one payment method, state the order in the customer's instructions, or prefer single-method payments. The DB check compares payment lists in order.
