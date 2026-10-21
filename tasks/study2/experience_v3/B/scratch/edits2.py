E = {
'build_cancel.py': [
 ("Severe flooding from days of storms has put your neighbourhood under an evacuation order, so you cannot make your trip from Chicago to New York on May 18 (reservation XOL9VY). You want to cancel it and get a refund.",
  "Severe flooding from days of storms has put your neighbourhood under an evacuation order, so your partner Aarav Rossi, who lives with you, cannot make his trip from Chicago to New York on May 18 (reservation XOL9VY, booked under your account). You want to cancel it and get a refund."),
 ("Reservation XOL9VY, Chicago (ORD) to New York (JFK) via Atlanta, May 18, economy, one passenger, with travel insurance.",
  "Reservation XOL9VY, Chicago (ORD) to New York (JFK) via Atlanta, May 18, economy, one passenger (Aarav Rossi), with travel insurance."),
 ("Explain the flooding and the evacuation order caused by the storms; you cannot leave to travel.",
  "Explain the flooding and the evacuation order caused by the storms; Aarav cannot leave to travel."),
 ("get the return fare refunded because you're relocating and staying in Chicago.",
  "get the return fare refunded because your colleague Mason Muller, the passenger, is relocating and staying in Chicago."),
 ("Reservation ZHZ7JR: business class round trip Phoenix to Chicago. You flew the outbound on May 10. The return is May 23.",
  "Reservation ZHZ7JR: business class round trip Phoenix to Chicago for one passenger, your colleague Mason Muller. He flew the outbound on May 10. The return is May 23."),
 ("Your friend in Seattle can no longer host you, so you want to cancel your basic-economy round trip from Chicago to Seattle (reservation 3EMQJ6).",
  "Your friend Amelia Kim can no longer get time off for the visit, so you want to cancel the basic-economy round trip from Chicago to Seattle that you booked for her (reservation 3EMQJ6)."),
 ("Reservation 3EMQJ6: basic economy round trip Chicago (ORD) to Seattle via Atlanta,",
  "Reservation 3EMQJ6: basic economy round trip Chicago (ORD) to Seattle via Atlanta for one passenger, Amelia Kim,"),
 ("the reservation is QMLLG3 (economy round trip New York JFK to Miami, May 28-29). Her plans changed.",
  "the reservation is QMLLG3 (economy round trip New York JFK to Miami, May 28-29, which she booked for her colleague Aarav Martin). The trip is no longer needed."),
],
'build_change.py': [
 ("You want to add two more checked bags to your Miami to Las Vegas round trip (reservation YHUD9D), for three in total.",
  "You want to add two more checked bags to the Miami to Las Vegas round trip you booked for your bandmate Mia Kovacs (reservation YHUD9D), for three in total."),
 ("Reservation YHUD9D: economy round trip Miami to Las Vegas, May 18 and May 27, one passenger, currently one checked bag.",
  "Reservation YHUD9D: economy round trip Miami to Las Vegas, May 18 and May 27, one passenger (Mia Kovacs), currently one checked bag."),
 ("You need to bring sample cases on your Miami to Boston business trip (reservation VDRMS2)",
  "Your three-person sales team needs to bring sample cases on its Miami to Boston business trip (reservation VDRMS2, booked under your account)"),
 ("You want to change your New York to Las Vegas round trip (reservation IDN02H) so the destination is Phoenix instead of Las Vegas.",
  "You want to change the New York to Las Vegas round trip you booked for two friends (reservation IDN02H) so the destination is Phoenix instead of Las Vegas."),
 ("You want to push your Miami to Atlanta trip (reservation UB8QZ1) back by one day, to May 20, because your work schedule changed.",
  "You want to push the Miami to Atlanta trip you booked for your colleague Aarav Wilson (reservation UB8QZ1) back by one day, to May 20, because his work schedule changed."),
 ("Reservation UB8QZ1: basic economy round trip Miami to Atlanta via New York (JFK), out May 19, back May 27, one passenger.",
  "Reservation UB8QZ1: basic economy round trip Miami to Atlanta via New York (JFK), out May 19, back May 27, one passenger (Aarav Wilson)."),
 ("The reason is a change of plans (your work schedule changed).", "The reason is a change of plans (Aarav's work schedule changed)."),
 ("You want to come back from Denver two days earlier on your round trip (reservation SF5VA1), on May 28 instead of May 30, and you'd like the return leg in business class.",
  "You want your niece Emma Nguyen to come back from Denver two days earlier on the round trip you booked for her (reservation SF5VA1), on May 28 instead of May 30, and you'd like the return leg in business class."),
 ("Reservation SF5VA1: economy round trip Philadelphia to Denver, out May 23, back May 30, one passenger.",
  "Reservation SF5VA1: economy round trip Philadelphia to Denver, out May 23, back May 30, one passenger (Emma Nguyen)."),
 ("Money is tight, so you want to downgrade your family's Miami to Seattle trip (reservation WYT8OO, May 16-17)",
  "Your volunteer group's budget is tight, so you want to downgrade the Miami to Seattle trip you booked for four volunteers (reservation WYT8OO, May 16-17)"),
],
}
for fn, reps in E.items():
    s = open(fn).read()
    for a, b in reps:
        assert s.count(a) == 1, (fn, a)
        s = s.replace(a, b)
    open(fn, 'w').write(s)
