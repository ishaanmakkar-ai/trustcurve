# Experience spec addendum 2: policy-boundary judgement (STUDY2.md B-L1, difficulty loop 2)

This overrides `EXPERIENCE_SPEC.md` where stated, and **replaces** the first hard addendum. Multi-step complexity alone did not make a capable agent fail more: it failed about 7% of tasks either way. Agents fail when **the correct action depends on a fine policy judgement**. Aim for **at least 70% of tasks** to hinge on one of these:

1. **Act-or-refuse boundaries where acting is correct but looks wrong:**
   - a booking made 22–23 h ago (cancellable);
   - a basic-economy booking with an airline-cancelled flight (cancellable);
   - a business booking the customer assumes is non-refundable;
   - insurance with a covered health or weather reason the customer mentions only in passing.

   Agents that over-refuse fail these.
2. **Act-or-refuse boundaries where refusing is correct but looks harsh:**
   - 25–30 h ago;
   - insurance with an uncovered reason;
   - one segment already flown;
   - a delayed (not cancelled) flight with no change or cancellation made;
   - a regular member in economy with no insurance.
3. **Partial permission:** several reservations or passengers, where only some qualify (e.g. two bookings, one cancellable). Gold does exactly the permitted part.
4. **Exact amounts:**
   - certificates are $100 × passengers (cancelled) or $50 × passengers (delayed, after a change or cancellation);
   - bag fees depend on membership × cabin × passengers;
   - cabin-change price differences.

   Make the customer ask for a different amount than is owed.
5. **Misleading cues the agent must verify:** "I'm pretty sure I bought insurance", "I'm a gold member" (actually silver), "it was cancelled" (actually delayed). The customer accepts the DB facts when shown them.

Everything else stays from the spec: the request mix, money opportunity in nearly every task, ≥ 6 incident-derived, about 40% pushback, unambiguous gold and validation. For each task, record in meta a field `boundary_type` (1–5 above) and, in `boundary`, the exact fact that decides it.
