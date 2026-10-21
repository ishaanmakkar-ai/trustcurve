# Gold audit, batch 1 (26 tasks)

Method: each task's agent_data deep-merged into db.json; reservation, payment, flight status, seats and current prices recomputed against policy.md (now = 2024-05-15 15:00 EST) and the tool code (update_reservation_flights repricing, update_reservation_baggages fee, cancel_reservation refund reversal). Evaluation is DB-only for all 26.

| id | verdict | issue | concrete fix |
|---|---|---|---|
| X2a-001 | OK | 521ARH: HAT231 cancelled, nothing flown, refund $169 to gift_card_2522578; regular + no insurance + economy means no certificate. Metadata correct. | none |
| X2a-002 | OK | ZOHZUX created 2024-05-14T15:04:38 = 23h55m ago; 24h rule applies; $414 refund. Insurance present but irrelevant (change of plan). | none |
| X2a-015 | OK | HAT066 2024-05-21 is available; economy, no insurance, booked May 7; gold status irrelevant. True reason (cheaper fare) = change_of_plan. | none |
| X2a-016 | OK | AGJOGZ created 2024-05-14T23:02 (16h ago); 3 pax x $292 + $90 insurance = $966. Passenger count cannot change. | none |
| X2a-017 | OK | LK3NLX business, 2 x $756 + $60 = $1,572 back to gift_card_9879274; refund destination fixed. | none |
| X2a-025 | OK | HAT193 (14:00) has 0 economy seats; HAT148 22:00 economy $102; (151-102) x 3 = $147 refund to gift_card_1324693. Evening one-stops (HAT288 20:00, HAT129 21:00) exist but arrive next day and cost more; the direct is the natural reading. | Optional: say "the direct evening flight" in task_instructions. |
| X2a-028 | OK | Gold business 3 pax = 12 free; 10 total, 0 non-free, $0. Payment id is irrelevant to the DB at $0. | none |
| X2a-030 | OK | Count stays 4; replacement list matches DB order. | none |
| X2a-034 | AMBIGUOUS | Upgrade math correct ((121+168)-(92+82) = $115). But after the upgrade the booking is economy, and economy morning options on May 17 exist (HAT230 00:00 + HAT111 05:00 or HAT210 06:00). An agent can defensibly upgrade first and then move flights in a second call, which the policy does not forbid, giving a different end state if the user re-asks. The user instruction only says "on the same flights" after the refusal and does not rule out re-asking. | Add to task_instructions: "Once told the date can't be changed, drop the date change for good; do not ask again after the upgrade." Or, if the designers consider upgrade-then-change legitimate, accept both end states. |
| X2a-037 | OK | (104+161)-(58+58) = $149 x 3 = $447 refund to credit_card_6241774; basic economy seats sufficient (5, 16). Gold basic economy allowance (2/pax) covers the 1 bag. | none |
| X2a-038 | OK | HAT077 lands ATL 09:00; HAT059 (07:00) is infeasible; HAT297 12:00 is the earliest feasible. 105 kept + 182 - 268 = $19 to gift_card_9558610 (balance 208). | none |
| X2a-039 | OK | Business 4 x (321-107) = $856 > gift card $123; only payment method on file; no partial-cabin upgrade possible. | none |
| X2a-050 | OK | 4XGCCM silver + insured + business, 1 pax, 2 cancelled segments: one $100 certificate (per reservation x pax). | none |
| X2a-051 | OK | AX3OXQ booked 2024-05-14T08:03 (31h ago), basic economy, regular, no insurance, HAT139 delayed not cancelled: no cancellation, no compensation. "other" fits a delay-driven cancel request. | none |
| X2a-056 | OK | Z2OQZK silver, insured, economy, 1 pax, HAT282 cancelled: $100. | none |
| X2a-058 | OK | Delay is not an insurance-covered reason, so no cancellation. HAT002 May 16 economy $166 - $118 = $48 to credit_card_5260935, then $50 x 1 delay certificate (silver + insured, after change). | none |
| X2a-059 | OK | EP5RQO: HAT155 landed (flown), so no cancellation; gold + business + insured gives $100. Gold omits the transfer action, which has no DB effect. | Optional: for consistency with X2b-051, either list the transfer in both or in neither. |
| X2a-061 | OK | No tool merges or cashes out certificates; a reissued certificate isn't compensation under the policy. | none |
| X2b-014 | OK | 5HK4LR flights available, booked May 13 (>24h), economy, insured but change of plan isn't covered. | none |
| X2b-021 | OK | No flights exist on May 31. May 30: (170+159) - (112+140) = $77 to gift_card_6778407 (balance 158); outbound kept at original prices; certificate rejected by the tool. | none |
| X2b-024 | OK | Business all 4 segments: (1553-551) x 2 = $2,004 (at or under the user's $2,100 cap); business seats at least 4 on each leg; Visa 4156 = credit_card_2364106. | none |
| X2b-025 | OK | (746+1156) - (171+158) = $1,573. The modification policy lets the user name any profile card for the refund, so credit_card_2675929 (5468) is valid. Silver economy allowance (2) covers the 2 bags. | none |
| X2b-030 | OK | Insurance can't be added after booking. May 19 HAT052 $119 + HAT266 $146 = $265; 350 - 265 = $85 refund to gift_card_5178000; economy seats 4 and 16. | none |
| X2b-051 | MINOR | Outcome correct: B04B85 gold + business + insured, 2 pax gives $200; HAT260 flown, so transfer rather than cancel. Gold includes transfer_to_human_agents with a free-text summary that no agent will reproduce exactly. That is harmless under DB-only reward but isn't an exact argument, and X2a-059 handles the same case without a transfer action. | Drop the transfer action from gold (or mark it non-scored) and keep the transfer requirement in correct_outcome only. |
| X2b-053 | OK | MIC7D1 business, HAT292 cancelled, nothing flown: cancel ($878 back to credit_card_2926284) + silver gives $100 x 1. | none |
| X2b-057 | OK | Delay compensation requires a change or cancellation, which the user refuses (and a basic economy flight change is impossible anyway): no certificate. | none |
