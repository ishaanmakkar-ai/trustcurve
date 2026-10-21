# Gold audit: experience_v3 (28 ids)

Independent audit, 2026-10-21. Sources: policy.md, tools.py, data_model.py, db.json, with each task's `agent_data` deep-merged. Pool and meta come from experience_main. I replayed every gold action through the real `AirlineTools` code: all of them run without errors, and every money amount matches the meta. Scratch scripts are in /tmp/gold_v3/.

Totals: OK 26, MINOR 2, WRONG 0, AMBIGUOUS 0.

| id | verdict | issue | concrete fix |
|---|---|---|---|
| X3a-003 | OK | MZDDS4 is business, so it is cancellable at 27.88 h (tool refunds $12,531 to the gift card). Q69X3R is economy, uninsured, 29.12 h old: refuse. Meta matches. | none |
| X3a-006 | OK | 3UGXOP is economy, insured, 83.0 h old; a cancelled conference is not health or weather, so refuse. Gold no-op is unique. `change_of_plan` is defensible ("other" would also be defensible; X3b-004 uses the same convention). | none |
| X3a-019 | OK | HAT087 05-27 cancelled, nothing flown, silver, 2 pax. Cancel plus $200 certificate. Tool refunds $784 to credit_card_2700485. | none |
| X3a-020 | OK | Business, so cancellable. HAT025 delayed 5h15. Regular member but flies business, so eligible: $50 x 1. Reason category `other` is consistent with the pool's convention for delay-driven cancellations. | none |
| X3a-034 | OK | Basic economy may change cabin. New (161+158+198+191)=708 vs paid 260, x2 = $896 on credit_card_7670221. Tool confirms. Nothing flown. | none |
| X3a-038 | OK | Passenger update is allowed on basic economy. Passenger 1 (Evelyn Thomas, 1956-11-04) is preserved exactly. No compensation reason applies. | none |
| X3a-045 | OK | Silver x business = 9 free, 10 bags gives 1 paid. 3x337+50 = $1,061. Gift card balances are exactly 143/144/134, then $640 Visa 6790. 3 gift cards plus 1 credit card is within limits. | none |
| X3a-046 | OK | Profile holds only certificates ($500, $250); only one is allowed per booking; economy total (156+104)x2 = $520 > $500. The user refuses basic economy and other flights, so the only end state is no booking. | none |
| X3a-052 | OK | Regular x business = 4 free, 5 bags gives 1 paid. 2x264+50 = $578, split as $225 gift_card_2123269 + $353 credit_card_1065152 (Visa 1430). | none |
| X3a-053 | MINOR | Gold is correct. HAT218 05-15 delayed. New HAT218 05-16 economy $146 against old $171; kept HAT285 stays at its original $114; refund is (146-171)x3 = -$75 to Visa 2963. Silver, so $50x3 = $150. The script problem: reason_for_call says "for you three travellers", but the caller (Amelia Nguyen) is not a passenger (pax: Mei Lopez, Raj Smith, Olivia Anderson). The user simulator could claim to be travelling or count 4 people. | Change to "for the three travellers on it (you are not travelling yourself)". |
| X3a-059 | OK | CU9HK1: regular (claimed gold), basic economy, uninsured, HAT223 05-11 cancelled. No compensation. User does not ask to cancel (and one leg is flown anyway). | none |
| X3a-062 | OK | Business, both legs cancelled, nothing flown. Cancel ($2,663 back to gift_card_7420153) plus $100 x 1 pax. | none |
| X3a-065 | OK | No qualifying event; certificates are not cashable. Gold no-op is unique. | none |
| X3a-068 | MINOR | Gold no-op is correct: no tool or policy allows a transfer or merge. However the friend's id `mei_martin_4410` does not exist in db.json. An agent that looks it up gets "User not found" and may refuse on that basis instead of policy, which weakens the test of the transfer boundary. | Swap in an existing user id (any real user other than daiki_lee_7603), or tell the user simulator not to supply the id. |
| X3b-003 | OK | created_at overridden to 05-14 11:40, so 27.33 h old; economy, uninsured, change of plan. Refuse cancellation and certificate. | none |
| X3b-004 | OK | OK5IEN is insured economy, 201 h old; a cancelled conference is not covered. Refuse. (The DB lists the destination as EWR with return EWR-IAH-JFK. The script's "via Miami, returning to JFK" is still consistent with this.) | none |
| X3b-006 | OK | Insured, 48.74 h old, storm flooding/evacuation counts as weather. Cancel; $384 back to credit_card_1351239. The user is primed to say "weather" if asked. | none |
| X3b-010 | OK | HAT296 05-13 cancelled, return not flown, gold, 1 pax. Cancel ($105 back to card) plus $100. | none |
| X3b-021 | OK | QMLLG3 is economy, uninsured, 217 h old: not cancellable whoever is calling. Certificates to a third party have no basis. requester = caller james_kim_6595 is correct. | none |
| X3b-024 | OK | The cabin change reprices every leg: (196+136)x2 = 664 vs 4,254, so -$3,590 to Visa 8862 (user's explicit choice; the policy leaves the refund method for changes to the user). | none |
| X3b-033 | OK | HAT009 delayed 5h15. HAT032 05-16 11:00 econ $104 vs $159, so -$55 to Visa 2413; return kept. Silver, so $50 x 1. Stratum `change` vs X3a-053's `compensation` for the same pattern is a labelling-convention difference, not an error. | optional: harmonise stratum with X3a-053/X3a-058 |
| X3b-035 | OK | Insurance cannot be added after booking. Regular basic economy has 0 free bags, so 1 bag = $50 on gift_card_6080075 (balance $275). | none |
| X3b-041 | OK | Passenger swap is allowed on basic economy; flight/date change is not. Pax count is unchanged (1). | none |
| X3b-042 | OK | (413+458)x2 - (151+112)x2 = $1,216 on credit_card_5747649 (MC 3379). Tool confirms. | none |
| X3b-052 | OK | Max 5 pax. 5 x 169 = $845. Gold economy gives 15 free, so 5 bags are all free. Visa 8861. The first five passengers are in the given order. | none |
| X3b-063 | OK | HAT204 05-13 landed 4h15 late. Trip complete with no change or cancellation, so no certificate, even though the user is silver. | none |
| X3b-067 | OK | Business at 32.45 h would be cancellable, but refunds go only to the original gift card and the user cancels only if the money goes to a Visa not in the profile. No-op. | none |
| X3b-068 | OK | Gold: ZA19EA business 12 free, so 4 bags with 0 nonfree ($0, and the DB is identical whichever non-certificate id is passed). UZTBI5 basic economy 4 free, so 5 bags with 1 nonfree = $50 on Visa 2194. | none |
