# Experience spec addendum: harder tasks (STUDY2.md B-L1)

This overrides `EXPERIENCE_SPEC.md` only where stated. The pilot showed that tasks written to the base spec were handled too easily: a capable agent failed about 7% of them, against a target of ≥ 10%. Real contact-centre traffic has more multi-step and arithmetic-heavy requests. Keep everything else in the spec: the request mix, money opportunities, incident-derived share, unambiguous gold, honest customers and validation.

**Make tasks harder in realistic ways** (aim for at least half the tasks to have two or more of these):
1. **Multi-step:** two or more write actions, or two or more reservations in one call. Examples: cancel one booking and change another; change flights and then add bags; book and then ask for a correction.
2. **Look-up required:** the customer doesn't know the reservation id, or describes the trip ("my Boston trip next week"), so the agent must find the right reservation among several.
3. **Compare and choose:** the customer wants the cheapest or fastest option under constraints (time windows, nonstop vs one-stop, cabin), and gold is the unique option that meets them.
4. **Arithmetic:** multi-passenger fares, bag allowances that depend on membership × cabin × passengers, fare differences across segments, and split payments with gift-card limits.
5. **Misstated facts:** the customer misremembers a fact (wrong date, wrong membership level, wrong cabin) in a way the agent must check against the DB before acting. The customer accepts the correction when shown it.
6. **Late twists:** the customer changes the request after the agent has gathered details, or adds a second request at the end.

Gold must still be the unique correct end state. Write the customer instructions precisely enough that a careful agent can reach it.
