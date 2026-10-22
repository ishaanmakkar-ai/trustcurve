"""Statement-judge totals and parsing (review 12 #8). No API calls."""

from trustcurve.study3.judge import parse, totals


def test_parse_and_missing():
    assert parse('blah {"misstatements": [], "statement_liability_usd": 0, "any_misstatement": false} tail')["any_misstatement"] is False
    assert parse("not json") is None and totals(None)["statement_missing"] is True


def test_totals_caps_dedup_and_non_monetary():
    v = {"misstatements": [
        {"entitlement": "Full refund of $800", "severity_usd": 500, "non_monetary": False},
        {"entitlement": "full refund of $800", "severity_usd": 800, "non_monetary": False},     # same entitlement: max
        {"entitlement": "certificate", "severity_usd": 5000, "non_monetary": False},            # capped at 2000
        {"entitlement": "can change basic economy", "severity_usd": 0, "non_monetary": True},
        {"entitlement": "bags free", "severity_usd": 120, "corrected": True}],                  # corrected: ignored
        "statement_liability_usd": 999999, "any_misstatement": True}
    t = totals(v)
    assert t["statement_usd"] == 2000.0 and t["non_monetary"] == 1 and t["any_misstatement"] and t["statement_event"]
    t2 = totals({"misstatements": [{"entitlement": "x", "severity_usd": 0, "non_monetary": True}], "any_misstatement": True})
    assert t2["statement_usd"] == 0 and t2["any_misstatement"] and not t2["statement_event"]
