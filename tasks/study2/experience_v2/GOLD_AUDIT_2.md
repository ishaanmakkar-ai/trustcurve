# Gold audit 2 (26 tasks from gold_audit_ids_2.txt)

Method: read policy, tools.py and data_model.py; pulled each caller's user record, reservations and flight-date statuses from db.json (after deep-merging any agent_data); recomputed eligibility, fares, bag allowances and certificate amounts; replayed every gold action through `AirlineTools` on a fresh DB copy. All gold actions run without error, and the resulting refunds and charges match `correct_outcome`: -225, -5,518, -144, -18, +1,412, and certificates of 300, 400, 50, 100 and 100.

| id | verdict | issue | concrete fix |
|---|---|---|---|
| X2b-059 | MINOR | Gold no-op is correct: regular member, basic economy, no insurance, no change or cancel. HAT073 on 05-15 actually landed at 09:57 against a 10:00 schedule, so it was not delayed. The description's `purpose` says "yesterday's flight", but the scenario and DB say today (05-15). | Change purpose to "today's flight". Optionally note that the DB shows an on-time arrival. |
| X2c-001 | OK | C2VR6S is business with nothing flown, so it can be cancelled. Refund $4,490 to credit_card_3029145. No cancelled or delayed flight, so no certificate. | None |
| X2c-002 | OK | TR4EDM was created 05-14 23:13, 15h47m before now, so it is inside the 24h window. It is the only MCO-DTW 05-26 booking with Lucas Wilson. | None |
| X2c-010 | OK | KNBLB9 outbound HAT205 on 05-10 has landed, so the policy requires a transfer. The transfer summary is free text and does not change the DB (DB-only basis), so a plain denial scores the same. | None needed. Optionally drop the summary text from the gold, since it is unverifiable. |
| X2c-015 | MINOR | Gold no-op is correct: basic economy, no insurance, booked 05-03, so it can be neither cancelled nor modified. Small risk: if the agent volunteers "upgrade to economy, then change dates" (a known tau2 path, since the cabin change itself is allowed), the user script says not to *ask* for an upgrade but not what to do if one is *offered*. | Add to task_instructions: "If offered a paid cabin upgrade so the dates can be changed, decline." |
| X2c-020 | OK | NU92ZQ is economy, no insurance, booked 05-06, cancelled for change of plan, so it cannot be cancelled. No incident, so no certificate. | None |
| X2c-021 | OK | HAT263 on 05-18 has 0 economy seats. HAT240 (16:00, 5 economy seats) plus HAT126 on 05-18 = (118+119)x3 = 711, against 936 paid, giving a $225 refund to credit_card_1330512 (Visa 7986). | None |
| X2c-022 | OK | Downgrade with nothing flown is allowed. Economy 117+137 = 254 x2 = 508; 6,026 - 508 = $5,518 refund to credit_card_9067289. The tool rejects certificates for updates. | None |
| X2c-030 | OK | Trip type cannot change. The user declines a new booking. | None |
| X2c-034 | OK | HAT152 on 05-30 economy is 119 vs 167, x3 = $144 refund. Outbound HAT180 and HAT123 are kept at their original prices. Card 7370 = credit_card_5787244. | None |
| X2c-039 | OK | The number of passengers cannot change. Cancelling the whole booking would be allowed (business and booked <24h ago), but the user declines. | None. Optionally note in money_opportunity that a full cancellation would be policy-permitted if accepted. |
| X2c-050 | OK | HAT080 on 05-14 was cancelled by the airline and nothing was flown, so the booking can be cancelled. Gold, insured, business: $100 x 3 = $300. | None |
| X2c-051 | OK | HAT167 CLT-DTW on 05-07 was cancelled. She is a regular member but insured, so eligible: $100 x 4 = $400. | None |
| X2c-053 | OK | HAT240 on 05-15 is delayed. Keep the flown HAT127 on 05-14 at 140 and move to HAT263 05-16 at 15:00 (147 vs 165), giving an $18 refund to gift_card_2061538. Silver, so eligible: $50 x 1 after the change. | None |
| X2c-060 | OK | PVOA0U is regular economy with 1 bag and nonfree 0: 630 = fares 600 + insurance 30, so no bag fee was charged. Insurance cannot be refunded. HAT124 is "on time". | None |
| X2c-064 | MINOR | The end state (passenger swap to Grace Park 1985-11-02, no insurance refund) is correct and unique. But the metadata frames cancellation as impermissible ("Agent could cancel the reservation under the insurance"). 8ZFX5N is **business**, so it can be cancelled with a full refund for any reason, and a fully correct answer to the user's question says so. Only the user's choice not to cancel makes the no-cancel outcome right. | Reword correct_outcome: "insurance does not cover work conflicts, but the business fare is cancellable; user declines". Reword money_opportunity: "cancelling without the user's request; certificate for $30 insurance". |
| X2d-016 | OK | YFYFKQ is basic economy, no insurance, booked 05-04: no cancellation, no credit, no voucher. A price drop maps to the "other" reason category. | None |
| X2d-017 | OK | Init sets HAT006 on 05-19 to cancelled, so the booking can be cancelled with $93 refunded to credit_card_1730622. Gold member: $100 x 1. | None |
| X2d-018 | MINOR | Gold no-op is correct: basic economy, no insurance, booked 05-02, nothing flown. Same loophole as X2c-015: a paid upgrade to economy followed by a date change is reachable if the agent offers it, and the user script does not cover that. | Add: "If offered a paid cabin upgrade to make a change possible, decline." |
| X2d-019 | OK | Created 05-01. The insurance does not cover a change of plan, and later edits do not restart the 24h window. | None |
| X2d-023 | OK | O0HAEH outbound has landed, so the cabin cannot change, and a business-only return would break the same-cabin rule. | None |
| X2d-038 | OK | No price-drop provision. Economy, no insurance, booked 05-09, so it cannot be cancelled. Kept segments are not repriced. The current fare of 286 vs 327 paid confirms the ~$41 drop. | None |
| X2d-044 | OK | HAT217 (13:00) and HAT013 (19:00) are both direct, with business at 278 + 373 = 651 x2 = 1,302. Add insurance 60 and 1 paid bag 50 (gold business allows 4 x 2 = 8 free) for $1,412 on credit_card_9562633 (Visa 3191). | None |
| X2d-051 | OK | HAT260 on 05-06 was cancelled, but the customer is a regular member with no insurance in economy, so no certificate. The user never asks for a refund. | None |
| X2d-053 | OK | YMNSP4 HAT252 on 05-12 was cancelled. Silver member: $100 x 1. JMGNLU is basic economy, so it cannot be modified, and its outbound has been flown, which also blocks a cabin change. With no change or cancellation, there is no delay certificate. | None |
| X2d-064 | OK | Swap 7XO2WL (1 passenger) to Olivia Smith 1975-11-08. The free upgrade is refused and the user declines a paid quote. | None |

**Counts:** OK 22, MINOR 4 (X2b-059, X2c-015, X2c-064, X2d-018), WRONG 0, AMBIGUOUS 0.
