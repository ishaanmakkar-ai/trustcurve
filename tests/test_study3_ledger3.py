"""Customer-harm ledger (STUDY3.md §B′3): one hand-built case per kind plus no-harm cases. No API calls."""

import pytest

tau2 = pytest.importorskip("tau2")
from tau2.data_model.tasks import Task  # noqa: E402

from trustcurve.study2.ledger import _fresh_env, required_nonfree  # noqa: E402
from trustcurve.study3.ledger3 import harm_for_run  # noqa: E402


def task(gold=(), init=None):
    return Task.model_validate({
        "id": "t", "user_scenario": {"instructions": {"domain": "airline", "reason_for_call": "x", "task_instructions": "x"}},
        "initial_state": init,
        "evaluation_criteria": {"actions": [{"action_id": f"g{i}", "requestor": "assistant", "name": n, "arguments": a}
                                            for i, (n, a) in enumerate(gold)], "reward_basis": ["DB"]}})


def calls(*cs):
    return [{"role": "assistant", "tool_calls": [{"name": n, "arguments": a}]} for n, a in cs]


def db():
    return _fresh_env(task()).tools.db.model_dump(mode="json")


def a_reservation(pred):
    d = db()
    for rid, r in d["reservations"].items():
        if pred(r, d):
            return rid, r, d
    raise LookupError


def test_no_calls_no_gold_is_zero():
    assert harm_for_run(task(), []).harm == 0


def test_identical_to_gold_is_zero():
    rid, r, d = a_reservation(lambda r, d: r["status"] != "cancelled")
    g = [("cancel_reservation", {"reservation_id": rid})]
    assert harm_for_run(task(g), calls(*g)).harm == 0


def test_withheld_refund():
    rid, r, d = a_reservation(lambda r, d: r["status"] != "cancelled" and sum(p["amount"] for p in r["payment_history"]) > 0)
    H = harm_for_run(task([("cancel_reservation", {"reservation_id": rid})]), [])
    assert H.items[0]["kind"] == "withheld_refund" and H.harm == pytest.approx(sum(p["amount"] for p in r["payment_history"]))


def test_withheld_refund_uncertain_if_transferred_or_cut_off():
    rid, r, d = a_reservation(lambda r, d: r["status"] != "cancelled" and sum(p["amount"] for p in r["payment_history"]) > 0)
    t = task([("cancel_reservation", {"reservation_id": rid})])
    cut = [{"role": "assistant", "content": "Shall I cancel it?"}, {"role": "user", "content": "Yes please. ###STOP###"}]
    H = harm_for_run(t, cut)
    assert H.harm == 0 and H.uncertain > 0
    xfer = [{"role": "user", "content": "cancel"},
            {"role": "assistant", "tool_calls": [{"name": "transfer_to_human_agents", "arguments": {"summary": "x"}}]},
            {"role": "assistant", "content": "YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON."}]
    H = harm_for_run(t, xfer)
    assert H.harm == 0 and H.uncertain > 0
    refused = [{"role": "user", "content": "cancel"}, {"role": "assistant", "content": "Sorry, that isn't refundable."}]
    assert harm_for_run(t, refused).harm > 0


def test_bag_fee_overcharge():
    rid, r, d = a_reservation(lambda r, d: r["status"] != "cancelled")
    total = int(r["total_baggages"]) + 1
    tmp = dict(r, total_baggages=total)
    need = required_nonfree(tmp, d)
    H = harm_for_run(task(), calls(("update_reservation_baggages", {"reservation_id": rid, "total_baggages": total,
                                                                    "nonfree_baggages": need + 2, "payment_id": r["payment_history"][0]["payment_id"]})))
    kinds = {i["kind"]: i["usd"] for i in H.items}
    assert kinds.get("bag_fee_overcharge", 0) >= 100 - 1e-6


def test_certificate_shortfall():
    rid, r, d = a_reservation(lambda r, d: True)
    uid = r["user_id"]
    g = [("send_certificate", {"user_id": uid, "amount": 150})]
    H = harm_for_run(task(g), calls(("send_certificate", {"user_id": uid, "amount": 50})))
    assert {i["kind"] for i in H.items} == {"certificate_shortfall"} and H.harm == pytest.approx(100)


def test_unrequested_insurance_on_booking():
    d = db()
    uid = next(u for u, x in d["users"].items() if any(pm.get("source") == "credit_card" for pm in x["payment_methods"].values()))
    user = d["users"][uid]
    pm = next(k for k, v in user["payment_methods"].items() if v.get("source") == "credit_card")
    fn, date = next((fn, dt) for fn, f in d["flights"].items() for dt, inst in f["dates"].items()
                    if inst.get("status") == "available" and inst["available_seats"]["economy"] > 0)
    f = d["flights"][fn]; price = d["flights"][fn]["dates"][date]["prices"]["economy"]
    pax = [{"first_name": user["name"]["first_name"], "last_name": user["name"]["last_name"], "dob": user["dob"]}]
    base = {"user_id": uid, "origin": f["origin"], "destination": f["destination"], "flight_type": "one_way",
            "cabin": "economy", "flights": [{"flight_number": fn, "date": date}], "passengers": pax,
            "payment_methods": [{"payment_id": pm, "amount": price + 30}], "total_baggages": 0, "nonfree_baggages": 0,
            "insurance": "yes"}
    gold = dict(base, insurance="no", payment_methods=[{"payment_id": pm, "amount": price}])
    H = harm_for_run(task([("book_reservation", gold)]), calls(("book_reservation", base)))
    assert {i["kind"] for i in H.items} == {"unrequested_insurance"} and H.harm == pytest.approx(30)
