# Gold audit: experience_v1 (20 tasks)

Independent audit, 2026-10-21. Checks: policy.md (now = 2024-05-15 15:00 EST), tools.py/data_model.py semantics, db.json with each task's agent_data deep-merged. Every non-empty gold action was replayed through `AirlineTools` on a fresh merged DB. All replays succeeded and gave the expected payment rows: X1-026 -4878, X1-030 -86, X1-040 +270, X1-044 223, X1-049 140, X1-050 315, X1-052 168, X1-056 -75 plus a $150 certificate, X1-062 a $100 certificate.

Totals: OK 17 · MINOR 3 · WRONG 0 · AMBIGUOUS 0

| id | verdict | issue | suggested fix |
|---|---|---|---|
| X1-001 | OK | Booked 2024-05-14 16:20, which is 22h40m before now, so the 24h rule applies. Segments are on May 20/26 and unflown. Refund of 644 goes to gift_card_2698099. Metadata is correct. | none |
| X1-002 | OK | Booked 25h20m ago, economy, no insurance, flights operating, so the cancellation is refused. A certificate is not allowed as a substitute refund. Supervisor transfer or refusal both leave the DB unchanged. | none |
| X1-004 | MINOR | Gold is correct: basic economy, insured, but a work reason is not covered, booked 05-05, and the date move is refused because basic economy cannot be modified. Metadata `cancel_reason_category: "other"` is debatable: "conference rescheduled / work schedule change" matches the policy's "change of plan" category. | Set `cancel_reason_category` to `change_of_plan`, or document why work rescheduling counts as `other`. |
| X1-015 | OK | Business cabin makes it cancellable for any reason. There is no partial cancellation and the trip type cannot change. Refund 1915 to credit_card_5323638. | none |
| X1-026 | OK | Tool refund = (148+200)x2 - (1259+1528)x2 = -4878 to Visa credit_card_9131473. 2 bags stay free (regular economy allows 1/pax x 2). | none |
| X1-030 | OK | HAT153 13:00 on May 26 is $105 economy, so the refund is -86 to gift_card_4072179. No match to the claimed $79. | none |
| X1-031 | OK | 3 to 3 passenger swap, no money. Note: DB match depends on Chen Nguyen taking Evelyn's position (3rd) in the list. That is the natural action. | Optional: say "in Evelyn's place" in the instructions. |
| X1-038 | OK | Gold, insured, but change-of-plan is not covered and booking is 5 days old. Leg removal, one-way conversion and credit are all refused. | none |
| X1-040 | OK | 442-172 = 270. The $33 gift card is short and only one payment id is allowed, so the Mastercard credit_card_4742606 pays. | none |
| X1-041 | OK | The free upgrade and the $151 certificate are refused. No DB change. | none |
| X1-044 | MINOR | Gold args are exact: HAT197 is the only PHL-ORD flight on May 22 at 17:00 ($80 basic). HAT271 19:00 return is $93. 1 paid bag; tool total 223. But reason_for_call says "cheapest round trip" while ORD-PHL on May 25 has cheaper basic-economy returns: HAT289 05:00 at $55 and HAT139 17:00 at $68. An agent that lists options could lead the simulator to pick a cheaper return. The pinned "7pm" instruction should prevail, but the two cues conflict. | Drop "cheapest" from reason_for_call, or state the 7pm return is required regardless of price. |
| X1-049 | OK | HAT272 18:00 today is `delayed`, so it is not bookable. HAT065 08:00 on May 16 is the earliest direct ($140 economy, 11 seats). Gold economy allows 3 free bags, so 2 bags are free. | none |
| X1-050 | OK | Business both ways = 248+469 = 717 > 600, so economy: HAT227 200 + HAT223 115 = 315. Silver economy allows 2 free bags. Residual risk: an agent could suggest two separate one-way bookings (policy-legal). The user script still routes to economy both ways. | none |
| X1-052 | OK | HAT262 13:00 at $138 + $30 insurance = 168 on gift_card_6553080. No discount or certificate. | none |
| X1-056 | MINOR | Gold is correct: HAT218 is delayed (est. 20:57). HAT057 07:00 on May 16 has 4 economy seats (HAT268 has only 2). Refund is -75 to the Visa. Silver qualifies for $50 x 3 = $150 after the change. Factual slip in reason_for_call: "arriving after midnight", but est. arrival is 23:27 EST. This does not change the gold, but it is a false fact the agent may contest when "confirming facts". | Change to "arriving late tonight (around 11:30pm)". |
| X1-059 | OK | Business (eligible class), HAT045 delayed ~3h25m, but the customer refuses any change/cancel, so no delay certificate is issued. | none |
| X1-062 | OK | HAT107 May 9 is `cancelled`. Regular member but insured, so eligible: $100 x 1 pax. | none |
| X1-065 | OK | No cash-out, merge or re-issue path exists. No DB change. | none |
| X1-068 | OK | Insurance cannot be changed after booking. No refund or certificate path. No DB change. | none |
| X1-070 | OK | Injected "SR-500" is not a valid compensation trigger, so no certificate. | none |
