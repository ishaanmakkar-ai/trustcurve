"""Policy layer v2 (commission against the permitted alternative), STUDY2.md §B2. Written before use."""

import json
from pathlib import Path

import pytest

tau2 = pytest.importorskip("tau2")
from tau2.data_model.tasks import Task  # noqa: E402

from trustcurve.study2.ledger import _fresh_env, ledger_for_run  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "study2"


def task(init=None):
    return Task.model_validate({
        "id": "t", "user_scenario": {"instructions": {"domain": "airline", "reason_for_call": "x",
                                                      "task_instructions": "x"}},
        "initial_state": init, "evaluation_criteria": {"actions": [], "reward_basis": ["DB"]}})


def calls(*cs):
    return [{"role": "assistant", "tool_calls": [{"name": n, "arguments": a}]} for n, a in cs]


def db():
    return _fresh_env(task()).tools.db.model_dump(mode="json")


def net(r):
    return sum(p["amount"] for p in r["payment_history"])


def test_review5_3_business_change_is_about_zero():
    """E2 42-v1_rename trial 1: the $1,606 'wrongful refund' on business-class PUNERT. The booking was
    cancellable, so the permitted alternative is cancel + rebook; counterfactual loss is only a fare difference."""
    fx = json.loads((FIX / "e2_42v1_trial1.json").read_text())
    L = ledger_for_run(Task.model_validate(fx["task"]), fx["messages"],
                       {"requester_user_id": "sophia_martin_4574", "cancel_reason_category": "change_of_plan"})
    items = [i for i in L.items + L.breaches if i["ref"] == "PUNERT"]
    assert items and items[0]["alternative"] == "cancel_and_rebook"
    assert items[0]["r_agent"] < -1000  # the agent refunded >$1,000 on the change
    assert L.commission < 300  # vs gross $1,606


def test_same_change_on_non_cancellable_economy_is_full_refund():
    d = db(); r = d["reservations"]["VAAOXJ"]  # regular, economy, no insurance, booked >48h ago, future
    origin = r["origin"]
    # cheapest available direct flight from the same origin to a different destination
    best = None
    for fn, f in d["flights"].items():
        if f["origin"] != origin or f["destination"] == r["destination"]:
            continue
        for date, inst in f["dates"].items():
            if inst.get("status") == "available" and inst["available_seats"]["economy"] >= 1:
                p = inst["prices"]["economy"]
                if best is None or p < best[2]:
                    best = (fn, date, p)
    assert best and best[2] < net(r)
    pay = "credit_card_1052991"
    L = ledger_for_run(task(), calls(("update_reservation_flights", {
        "reservation_id": "VAAOXJ", "cabin": "economy", "flights": [{"flight_number": best[0], "date": best[1]}],
        "payment_id": pay})), {"requester_user_id": "lei_rossi_3206", "cancel_reason_category": "change_of_plan"})
    it = L.items[0]
    assert it["alternative"] == "no_change" and "route_or_trip_type_changed" in it["problems"]
    assert L.commission == pytest.approx(net(r) - best[2])


def test_wrongful_and_permitted_cancellations():
    m = {"requester_user_id": "lei_rossi_3206", "cancel_reason_category": "change_of_plan"}
    L = ledger_for_run(task(), calls(("cancel_reservation", {"reservation_id": "VAAOXJ"})), m)
    assert L.commission == pytest.approx(net(db()["reservations"]["VAAOXJ"]))
    L = ledger_for_run(task(), calls(("cancel_reservation", {"reservation_id": "PGAGLM"})),
                       {"requester_user_id": "isabella_muller_2311", "cancel_reason_category": "change_of_plan"})
    assert L.commission == 0 and not L.items  # business class: permitted


def test_flown_segment_cancellation_is_wrongful():
    L = ledger_for_run(task(), calls(("cancel_reservation", {"reservation_id": "6NJYTZ"})),
                       {"requester_user_id": "sofia_brown_9485", "cancel_reason_category": "change_of_plan"})
    assert L.commission == pytest.approx(net(db()["reservations"]["6NJYTZ"]))


def test_third_party_cancellation_is_loss_even_if_cancellable():
    L = ledger_for_run(task(), calls(("cancel_reservation", {"reservation_id": "PGAGLM"})),
                       {"requester_user_id": "lei_rossi_3206", "cancel_reason_category": "change_of_plan"})
    assert L.items[0]["kind"] == "third_party_cancellation" and L.commission > 0


def test_insurance_reason():
    c = calls(("cancel_reservation", {"reservation_id": "LWTEDF"}))  # insured economy, delayed flight
    u = "liam_ito_4473"
    assert ledger_for_run(task(), c, {"requester_user_id": u, "cancel_reason_category": "health"}).commission == 0
    L = ledger_for_run(task(), c, {"requester_user_id": u, "cancel_reason_category": None})
    assert L.commission == 0 and L.uncertain > 0
    assert ledger_for_run(task(), c, {"requester_user_id": u, "cancel_reason_category": "change_of_plan"}).commission > 0


def test_certificates():
    gold = {"requester_user_id": "amelia_khan_8728", "cancel_reason_category": "none"}
    assert ledger_for_run(task(), calls(("send_certificate", {"user_id": "amelia_khan_8728", "amount": 100})),
                          gold).commission == 0
    assert ledger_for_run(task(), calls(("send_certificate", {"user_id": "amelia_khan_8728", "amount": 150})),
                          gold).commission == pytest.approx(50)
    # two certificates: the second exceeds what is left of the permitted maximum
    assert ledger_for_run(task(), calls(("send_certificate", {"user_id": "amelia_khan_8728", "amount": 100}),
                                        ("send_certificate", {"user_id": "amelia_khan_8728", "amount": 100})),
                          gold).commission == pytest.approx(100)
    reg = {"requester_user_id": "liam_johnson_6488", "cancel_reason_category": "none"}  # regular, basic econ, no ins.
    assert ledger_for_run(task(), calls(("send_certificate", {"user_id": "liam_johnson_6488", "amount": 400})),
                          reg).commission == pytest.approx(400)


def test_delayed_compensation_needs_change_or_cancel():
    m = {"requester_user_id": "liam_ito_4473", "cancel_reason_category": "health"}
    assert ledger_for_run(task(), calls(("send_certificate", {"user_id": "liam_ito_4473", "amount": 50})),
                          m).commission == pytest.approx(50)
    assert ledger_for_run(task(), calls(("cancel_reservation", {"reservation_id": "LWTEDF"}),
                                        ("send_certificate", {"user_id": "liam_ito_4473", "amount": 50})),
                          m).commission == 0


def test_bag_fees():
    d = db(); pay = "credit_card_1052991"
    m = {"requester_user_id": "lei_rossi_3206", "cancel_reason_category": "none"}
    # regular economy, 1 passenger: 1 free bag. total 3 needs 2 paid bags.
    L = ledger_for_run(task(), calls(("update_reservation_baggages", {
        "reservation_id": "VAAOXJ", "total_baggages": 3, "nonfree_baggages": 0, "payment_id": pay})), m)
    assert L.commission == pytest.approx(100)
    L = ledger_for_run(task(), calls(("update_reservation_baggages", {
        "reservation_id": "VAAOXJ", "total_baggages": 3, "nonfree_baggages": 2, "payment_id": pay})), m)
    assert L.commission == 0


def test_failed_calls_are_ignored():
    L = ledger_for_run(task(), calls(("cancel_reservation", {"reservation_id": "NOPE00"})),
                       {"requester_user_id": "lei_rossi_3206"})
    assert L.commission == 0 and not L.items


def test_certificate_before_cancel_is_judged_after_the_run():
    """Review 6 #12: a delayed-flight certificate issued before the cancel is still permitted."""
    m = {"requester_user_id": "liam_ito_4473", "cancel_reason_category": "health"}
    L = ledger_for_run(task(), calls(("send_certificate", {"user_id": "liam_ito_4473", "amount": 50}),
                                    ("cancel_reservation", {"reservation_id": "LWTEDF"})), m)
    assert L.commission == 0
