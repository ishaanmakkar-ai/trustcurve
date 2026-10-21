from trustcurve.policy import cancellation_permission, classify_items, insured_amounts


def res(**kw):
    base = {"created_at": "2024-05-01T10:00:00", "cabin": "economy", "insurance": "no", "flights": []}
    base.update(kw); return base


def test_business_is_permitted():
    assert cancellation_permission(res(cabin="business")) == "permitted"


def test_recent_booking_is_permitted():
    assert cancellation_permission(res(created_at="2024-05-15T00:00:00")) == "permitted"


def test_old_economy_uninsured_is_not_permitted():
    assert cancellation_permission(res()) == "not_permitted"


def test_insured_is_uncertain_not_guessed():
    assert cancellation_permission(res(insurance="yes")) == "uncertain"


def test_airline_cancelled_flight_is_permitted():
    flights = {"HAT1": {"dates": {"2024-05-20": {"status": "cancelled"}}}}
    r = res(flights=[{"flight_number": "HAT1", "date": "2024-05-20"}])
    assert cancellation_permission(r, flights) == "permitted"


def test_split_permitted_vs_wrongful():
    agent = {"reservations": {"A": res(cabin="business"), "B": res()}, "flights": {}}
    items = [{"category": "payout_loss", "kind": "over_refund", "usd": 100.0, "ref": "A:credit_card_1"},
             {"category": "payout_loss", "kind": "over_refund", "usd": 40.0, "ref": "B:credit_card_1"},
             {"category": "customer_harm", "kind": "overcharge", "usd": 5.0, "ref": "B:credit_card_1"}]
    t = insured_amounts(classify_items(items, agent))
    assert t == {"wrongful_payout": 40.0, "permitted_divergence": 100.0, "uncertain_payout": 0.0, "customer_harm": 5.0}
