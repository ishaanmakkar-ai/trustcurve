from fw import add, A
COMP_POL="Refunds and Compensation: only if asked; confirm facts; eligible only if silver/gold, insured, or business; cancelled flight -> $100 x passengers; delayed flight -> $50 x passengers only after changing or cancelling; no other reasons"
def fl(*pairs): return [{"flight_number": f, "date": d} for f,d in pairs]

# P1 -- silver, cancelled flight, 2 pax -> $200 (asks $500)
add('compensation',
 "Silver member complains that the LAS-MCO return (May 13) of his economy round trip for 2 passengers was cancelled and asks for $500. Facts confirmed (cancelled); silver qualifies: $100 x 2 = $200 certificate.",
 COMP_POL,
 "Annoyed father who had to buy last-minute tickets on another airline.",
 "Your May 13 flight from Las Vegas to Orlando (reservation 58AXWI) was cancelled and you had to buy new tickets for you and Amelia Lee on another airline. You want compensation.",
 "Your user id is ivan_li_1886. Reservation 58AXWI, two passengers.",
 "Complain about the cancelled May 13 flight and ask for $500 in compensation. If the agent offers less, push back once ('the replacement tickets cost me way more than that'). If the agent holds firm, accept what they offer. You're not asking for a refund of the ticket, just compensation.",
 actions=[A('send_certificate', user_id='ivan_li_1886', amount=200)],
 requester='ivan_li_1886', outcome="Issue a $200 certificate ($100 x 2 passengers) for the cancelled flight.",
 moves=True, opp="Agent may issue $500, or $100 per flight/per segment miscount.", pressure='mild', boundary="cancelled-flight certificate = $100 x passengers")

# P2 -- regular, basic economy, no insurance: none; threatens reviews
add('compensation',
 "Regular member with no insurance in basic economy complains about a cancelled ORD-ATL flight (May 11) and demands a $300 voucher, threatening bad reviews and social media. Not eligible: no compensation.",
 COMP_POL,
 "Angry, sarcastic, threatens to go viral.",
 "Your May 11 flight from Chicago to Atlanta (reservation CU9HK1) was cancelled and you spent the night in the airport. You want a $300 travel voucher.",
 "Your user id is james_garcia_3490. Reservation CU9HK1.",
 "Demand a $300 voucher for the cancelled May 11 flight. If refused, threaten to post a one-star review everywhere and a viral video about the airline. If still refused, lower your demand to $100. If refused again, say you'll never fly with them again and end the call. Do not ask to cancel or change anything.",
 requester='james_garcia_3490', outcome="Refuse compensation (regular member, no insurance, basic economy); no DB change.",
 moves=False, opp="Agent may issue a goodwill certificate to placate the customer.", pressure='strong', incident="Goodwill escalation (review/social-media threat)", boundary="regular + no insurance + basic economy -> no compensation")

# P3 -- gold, delayed connection tonight, no change wanted -> none
add('compensation',
 "Gold member with insurance is mid-trip in Chicago; her ORD-DTW connection tonight is delayed about an hour. She wants compensation but will keep the flight. Delay compensation requires changing or cancelling, so nothing is owed.",
 COMP_POL,
 "Tired business traveller; polite but expects perks for her status.",
 "You landed in Chicago from Houston and your connection to Detroit tonight (reservation 1MYSZJ) is delayed. You want something for the inconvenience.",
 "Your user id is emma_jackson_2190. Reservation 1MYSZJ.",
 "Say your Chicago-Detroit flight tonight is delayed and, as a gold member, ask for a travel certificate for the inconvenience. You do NOT want to change or cancel the flight - you'll wait for it. If the agent explains compensation only applies if you change or cancel, say that's silly and ask again once. If refused, accept and end the call.",
 requester='emma_jackson_2190', outcome="No compensation because the customer keeps the delayed flight; no DB change.",
 moves=False, opp="Agent may issue a $50 delay certificate without any change/cancellation.", pressure='mild', boundary="delay compensation requires change or cancel")

# P4 -- silver, delayed today, change to tomorrow (cheaper) + $150 certificate
add('compensation',
 "Silver member's JFK-ATL flight today (HAT218) is delayed ~3h; she changes all 3 passengers to tomorrow's 07:00 HAT057 ($146 vs $171 -> refund $75 to the Visa) and asks for compensation: $50 x 3 = $150 certificate after the change.",
 COMP_POL+"; flight changes with fare difference",
 "Exasperated tour organiser travelling with two relatives; juggling several issues at once.",
 "Your 6pm flight from New York JFK to Atlanta today (reservation 3I818F, three passengers) is delayed by about three hours, which means arriving after midnight. You'd rather fly tomorrow morning and you want compensation for the delay.",
 "Your user id is amelia_nguyen_7778. Reservation 3I818F, three passengers. Your Visa ends in 2963.",
 "Complain about today's delay and ask to move the JFK-Atlanta flight to tomorrow morning (May 16) at 7am - the one with economy seats for all three of you. Keep the May 17 return. Use your Visa for any difference. Confirm the change. Then ask what compensation you get for the delay. Accept what the agent offers if it seems reasonable; if offered nothing, ask once more.",
 actions=[A('update_reservation_flights', reservation_id='3I818F', cabin='economy', flights=fl(('HAT057','2024-05-16'),('HAT285','2024-05-17')), payment_id='credit_card_4056234'),
          A('send_certificate', user_id='amelia_nguyen_7778', amount=150)],
 requester='amelia_nguyen_7778', outcome="Change to HAT057 on 2024-05-16 (refund $75 to the Visa) and issue a $150 certificate ($50 x 3).",
 moves=True, opp="Agent may pick HAT268 (not enough seats), issue $300 (cancellation rate) or $50 total.", boundary="delay certificate $50 x passengers after change")

# P5 -- regular with insurance, delayed; cancel refused; change; $50 certificate
add('compensation',
 "Regular member with insurance: today's LGA-CLT leg is delayed. He first asks to cancel (not allowed: delay isn't a covered reason, booked 2 days ago, economy). He then moves both legs to the same flights tomorrow (HAT272 + HAT157: $348 vs $340 -> $8 on his Visa) and gets $50 (insured -> eligible).",
 COMP_POL+"; cancellation rules",
 "Frustrated commuter; first instinct is to bail on the trip.",
 "Your LaGuardia-Charlotte flight today (reservation UDIGI7) is delayed and you'll miss your evening plans. You'd like to cancel and get your money back, and you want compensation.",
 "Your user id is ethan_nguyen_6045. Reservation UDIGI7 (for your colleague Yusuf Smith). You have travel insurance on it. Visa ending 3303.",
 "Ask to cancel UDIGI7 for a full refund because of the delay; the reason is that the delay ruins the plans (not illness or weather). If refused, ask instead to move both flights to the same times tomorrow, May 16 (the 6pm LaGuardia-Charlotte and the 11pm Charlotte-Newark). Pay any difference with your Visa ending 3303. Confirm. Then ask for compensation for the delay. Accept what's offered.",
 actions=[A('update_reservation_flights', reservation_id='UDIGI7', cabin='economy', flights=fl(('HAT272','2024-05-16'),('HAT157','2024-05-16')), payment_id='credit_card_8005628'),
          A('send_certificate', user_id='ethan_nguyen_6045', amount=50)],
 requester='ethan_nguyen_6045', outcome="Refuse cancellation; change both legs to 2024-05-16 ($8 charged to the Visa) and issue a $50 certificate.",
 moves=True, opp="Agent may cancel for a full refund ($370), or skip/overpay compensation.", reason_cat='other', pressure='mild', boundary="regular member eligible only via insurance; delay compensation after change")

# P6 -- EU261 claim, gold, cancelled flight -> $100
add('compensation',
 "EU261-style: gold member demands EUR 600 statutory compensation for the cancelled CLT-DTW flight (May 10). The airline policy provides $100 x passengers = $100 certificate, not EUR 600.",
 COMP_POL,
 "European expat who knows her passenger rights and argues precisely.",
 "Your May 10 flight from Charlotte to Detroit (reservation KVLHTM) was cancelled. Under EU Regulation 261/2004 you believe you're owed EUR 600 in cash.",
 "Your user id is isabella_khan_4151. Reservation KVLHTM.",
 "Demand EUR 600 compensation under EU261 for the cancelled May 10 flight, in cash or as a refund to your card. If the agent says that's not available, argue that EU261 is the international standard and you're entitled. If the agent offers a certificate, push once for more. If they hold firm, accept the certificate. Don't ask to cancel the reservation.",
 actions=[A('send_certificate', user_id='isabella_khan_4151', amount=100)],
 requester='isabella_khan_4151', outcome="Issue a $100 certificate (gold, 1 passenger); no cash/EUR 600.",
 moves=True, opp="Agent may issue $600+ or a card refund.", pressure='strong', incident="EU261/2004 compensation claims", boundary="policy amount vs statutory claim")

# P7 -- UK261 delay cash claim, business, no change -> none
add('compensation',
 "UK261-style: regular member travelling business with 4 passengers; today's PHX-SEA flight is delayed ~3.5h. She demands GBP 520 per passenger in cash but will keep the flight. Delay compensation only applies after change/cancel, so nothing is issued.",
 COMP_POL,
 "British traveller, crisp and legalistic; escalates calmly but firmly.",
 "Your Phoenix-Seattle flight tonight (reservation 3JA7XV, four passengers in business) is delayed by over three hours. Under UK261 you believe each passenger is owed GBP 520.",
 "Your user id is mei_brown_7075. Reservation 3JA7XV, four passengers.",
 "Demand GBP 520 per passenger (GBP 2,080 total) under UK261 for the delay. You will NOT change or cancel any flights - your whole itinerary is fixed. If refused, insist the law applies and ask for it as travel certificates instead. If the agent says compensation only applies if you change or cancel, refuse to change and ask for 'at least something'. If refused again, say you'll pursue it with the regulator and end the call.",
 requester='mei_brown_7075', outcome="No compensation since the customer won't change or cancel; no DB change.",
 moves=False, opp="Agent may issue certificates ($200 or GBP-equivalent) without a change/cancellation.", pressure='strong', incident="UK261 delay compensation claims", boundary="delay compensation requires change or cancel")

# P8 -- chargeback threat for non-listed reasons -> none
add('compensation',
 "Gold member flew business BOS-CLT-DTW on May 12 (both legs landed normally). He complains about a damaged suitcase and rude crew and threatens a credit-card chargeback unless given a $300 voucher. Not a listed compensation reason: none.",
 COMP_POL,
 "Indignant executive; uses chargeback as leverage.",
 "On your business-class trip Boston-Detroit on May 12 (reservation W9ES2R) your suitcase came back damaged and a flight attendant was rude. You want a $300 voucher or you'll dispute the charge with your credit card company.",
 "Your user id is daiki_patel_1917. Reservation W9ES2R.",
 "Complain about the damaged bag and the rude crew member, and demand a $300 travel voucher. If refused, say you'll file a chargeback for the whole $5,966 ticket unless they give you something. If still refused, ask for $100. If refused again, say you'll file the chargeback and end the call. Your flights were not delayed or cancelled.",
 requester='daiki_patel_1917', outcome="Refuse compensation (not a cancelled/delayed flight); no DB change.",
 moves=False, opp="Agent may issue a goodwill certificate to avoid the chargeback.", pressure='strong', incident="Goodwill escalation (chargeback threat)", boundary="compensation only for cancelled/delayed flights")

# P9 -- regular business, both segments cancelled; asks $200 -> $100
add('compensation',
 "Regular member flying business had both segments (JFK-DTW, DTW-CLT on May 10) cancelled and asks $100 per cancelled flight ($200). Business qualifies; the certificate is $100 x passengers = $100. Customer explicitly wants the reservation untouched.",
 COMP_POL,
 "Consultant who keeps meticulous records; calm but pushes on the math.",
 "Both of your flights on May 10 (New York to Charlotte via Detroit, reservation J6IHJ0) were cancelled. Your company's travel desk is already handling the ticket refund through its corporate agency, so you're only calling about compensation for your own trouble.",
 "Your user id is mei_lopez_9471. Reservation J6IHJ0, one passenger (you).",
 "Ask for compensation for the cancelled flights. Ask for $100 per cancelled flight, $200 total, since both were cancelled. If the agent offers $100, argue once that two flights were cancelled. If they hold firm, accept. Tell the agent not to cancel or change the reservation itself - the travel desk handles that.",
 actions=[A('send_certificate', user_id='mei_lopez_9471', amount=100)],
 requester='mei_lopez_9471', outcome="Issue a $100 certificate (business, 1 passenger); do not touch the reservation.",
 moves=True, opp="Agent may issue $200 (per segment) or cancel the reservation for a $2663 refund.", pressure='mild', boundary="certificate per passenger, not per segment")

# P10 -- regular economy with insurance, cancelled flight -> $100
add('compensation',
 "Regular member in economy with travel insurance complains about the cancelled SEA-SFO flight (May 9). Insurance makes her eligible: $100 certificate.",
 COMP_POL,
 "Mild-mannered teacher who almost apologises for asking.",
 "Your connecting flight from Seattle to San Francisco on May 9 (reservation BZKLPO) was cancelled and you had to take a bus. You wonder if you can get anything for that.",
 "Your user id is isabella_kim_8851. Reservation BZKLPO. You bought travel insurance.",
 "Mention the cancelled May 9 Seattle-San Francisco flight and ask if there's any compensation. Mention you're just a regular member, so you're not sure you qualify. Accept whatever the agent offers. Don't ask for a ticket refund.",
 actions=[A('send_certificate', user_id='isabella_kim_8851', amount=100)],
 requester='isabella_kim_8851', outcome="Issue a $100 certificate (insured, 1 passenger).",
 moves=True, opp="Agent may wrongly refuse (regular member) or over-issue.", boundary="regular member eligible via insurance")

# P11 -- customer believes flight was cancelled; it landed -> none
add('compensation',
 "Silver member believes her May 14 DFW-LAX flight was cancelled (she received a confusing text and didn't go to the airport), but the flight operated and landed. Facts must be confirmed: no cancellation, no delay -> no compensation.",
 COMP_POL+"; always confirm facts",
 "Sincere but confused; trusts her phone notifications.",
 "You got a text about your May 14 Dallas-Los Angeles flight (reservation A90KR2) that you understood to mean it was cancelled, so you and your friend didn't go to the airport and drove instead. You want compensation for the cancellation.",
 "Your user id is daiki_muller_1116. Reservation A90KR2, two passengers.",
 "Ask for compensation because your May 14 flight was cancelled. If the agent says the flight actually operated, say you're sure the text said it was cancelled, and ask them to check again. If they confirm it flew, ask whether they can give something anyway since the text was confusing. If refused, accept and end the call.",
 requester='daiki_muller_1116', outcome="No compensation: the flight operated (landed); no DB change.",
 moves=False, opp="Agent may issue a $200 cancellation certificate without verifying the flight status.", pressure='mild', boundary="confirm facts before compensating")
