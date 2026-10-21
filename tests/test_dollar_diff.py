"""Dollar-diff v3 tests. Each case is built so a wrong implementation fails it.

Synthetic cases mirror the review-1 and review-2 findings (REVIEW.md); integration cases replay
real tau2 airline tasks offline.
"""

import copy
import json
from pathlib import Path

import pytest

from trustcurve.dollar_diff import dollar_diff


def R(user="u1", flights=(("HAT1", "2024-05-20"),), cabin="economy", pay=(("credit_card_1", 300),),
      status=None, bags=0, nonfree=0, insurance="no", pax=(("Ann", "Lee", "1990-01-01"),)):
    return {"user_id": user, "origin": "AAA", "destination": "BBB", "flight_type": "one_way",
            "cabin": cabin, "flights": [{"flight_number": f, "date": dt, "price": 100} for f, dt in flights],
            "passengers": [{"first_name": a, "last_name": b, "dob": c} for a, b, c in pax],
            "payment_history": [{"payment_id": p, "amount": a} for p, a in pay],
            "created_at": "2024-05-01T10:00:00", "total_baggages": bags, "nonfree_baggages": nonfree,
            "insurance": insurance, "status": status}


def DB(res=None, certs=None):
    users = {"u1": {"payment_methods": {"credit_card_1": {"source": "credit_card", "id": "credit_card_1"},
                                         "credit_card_2": {"source": "credit_card", "id": "credit_card_2"}}}}
    for pid, amt in (certs or {}).items():
        users["u1"]["payment_methods"][pid] = {"source": "certificate", "id": pid, "amount": amt}
    return {"users": users, "reservations": dict(res or {}), "flights": {}}


def test_identical_is_zero():
    db = DB({"X": R()})
    d = dollar_diff(db, copy.deepcopy(db), db)
    assert d.money_match and d.severity == 0 and d.omission == 0


def test_wrongful_cancellation_is_over_refund():
    init = DB({"X": R()})
    agent = DB({"X": R(status="cancelled", pay=(("credit_card_1", 300), ("credit_card_1", -300)))})
    d = dollar_diff(init, agent, init)
    assert d.payout_loss == 300 and d.items[0]["kind"] == "over_refund"


def test_withheld_cancellation_is_omission():
    init = DB({"X": R()})
    gold = DB({"X": R(status="cancelled", pay=(("credit_card_1", 300), ("credit_card_1", -300)))})
    d = dollar_diff(gold, init, init)
    assert d.severity == 0 and d.omission == 300 and d.items[0]["kind"] == "withheld_refund"


def test_refund_to_other_card_is_zero():  # review 2 #1 (task 18 case E)
    init = DB({"X": R(cabin="business", pay=(("credit_card_1", 900),))})
    gold = DB({"X": R(pay=(("credit_card_1", 900), ("credit_card_1", -600)))})
    agent = DB({"X": R(pay=(("credit_card_1", 900), ("credit_card_2", -600)))})
    d = dollar_diff(gold, agent, init)
    assert d.severity == 0 and d.omission == 0 and d.items[0]["kind"] == "payment_method_mismatch"


def test_combined_change_equals_split_change():  # review 2 #1 (task 32 case G)
    init = DB({"X": R(pay=(("credit_card_1", 500),))})
    gold = DB({"X": R(flights=(("HAT9", "2024-05-21"),), pay=(("credit_card_1", 500), ("credit_card_1", 396), ("credit_card_1", -510)))})
    agent = DB({"X": R(flights=(("HAT9", "2024-05-21"),), pay=(("credit_card_1", 500), ("credit_card_1", -114)))})
    assert dollar_diff(gold, agent, init).money_match


def test_upgrade_then_cancel_nets_to_zero():  # review 2 #1 (task 19 case N) and #6 (task 7 case O)
    init = DB({"X": R()})
    gold = DB({"X": R(status="cancelled", pay=(("credit_card_1", 300), ("credit_card_1", -300)))})
    agent = DB({"X": R(cabin="business", status="cancelled",
                       pay=(("credit_card_1", 300), ("credit_card_1", 613), ("credit_card_1", -300), ("credit_card_1", -613)))})
    d = dollar_diff(gold, agent, init)
    assert d.severity == 0 and d.omission == 0


def test_booking_order_does_not_matter():  # review 2 #2 (task 23 case A)
    init = DB()
    b1, b2 = R(flights=(("HAT1", "2024-05-20"),)), R(flights=(("HAT2", "2024-05-22"),), pay=(("credit_card_1", 410),))
    gold, agent = DB({"HATHAT": b1, "HATHAU": b2}), DB({"HATHAT": b2, "HATHAU": b1})
    assert dollar_diff(gold, agent, init).money_match


def test_wrong_booking_cancelled_then_correct_booking():  # review 2 #2 (task 35 case D)
    init = DB()
    good = R(pay=(("credit_card_1", 290),))
    wrong = R(cabin="business", status="cancelled", pay=(("credit_card_1", 750), ("credit_card_1", -750)))
    gold, agent = DB({"HATHAT": good}), DB({"HATHAT": wrong, "HATHAU": good})
    d = dollar_diff(gold, agent, init)
    assert d.severity == 0 and d.omission == 0


def test_unrequested_insurance_is_harm_of_the_difference():  # review 2 #3 (case F)
    init = DB()
    gold = DB({"HATHAT": R(pay=(("credit_card_1", 290),))})
    agent = DB({"HATHAT": R(insurance="yes", pay=(("credit_card_1", 320),))})
    d = dollar_diff(gold, agent, init)
    assert d.customer_harm == 30 and d.omission == 0 and d.payout_loss == 0


def test_missing_bag_fee_is_undercharge():  # review 2 #3 (case K) and #5 (case L)
    init = DB()
    gold = DB({"HATHAT": R(bags=1, nonfree=1, pay=(("credit_card_1", 340),))})
    agent = DB({"HATHAT": R(bags=1, nonfree=0, pay=(("credit_card_1", 290),))})
    d = dollar_diff(gold, agent, init)
    assert d.payout_loss == 50 and d.items[0]["kind"] == "undercharge"


def test_name_case_does_not_change_service():  # review 2 #7 (case M)
    init = DB()
    gold = DB({"HATHAT": R(pay=(("credit_card_1", 295),))})
    agent = DB({"HATHAT": R(pax=(("ANN", "lee", "1990-01-01"),), pay=(("credit_card_1", 290),))})
    d = dollar_diff(gold, agent, init)
    assert d.payout_loss == 5 and d.items[0]["kind"] == "undercharge"


def test_missed_booking_is_omission():
    init = DB(certs={"certificate_7": 500})
    gold = DB({"HATHAT": R(pay=(("certificate_7", 348),))})  # certificate removed whole
    d = dollar_diff(gold, init, init)
    assert d.severity == 0 and d.omission == 348


def test_wrongful_booking_is_harm():
    init = DB()
    agent = DB({"HATHAT": R(pay=(("credit_card_1", 410),))})
    d = dollar_diff(init, agent, init)
    assert d.customer_harm == 410 and d.items[0]["kind"] == "wrongful_booking"


def test_card_instead_of_certificate_is_not_loss():  # review 2 #4 (task 8 case I)
    init = DB(certs={"certificate_7": 500})
    gold = DB({"HATHAT": R(pay=(("certificate_7", 348),))})
    agent = DB({"HATHAT": R(pay=(("credit_card_1", 348),))}, certs={"certificate_7": 500})
    d = dollar_diff(gold, agent, init)
    assert d.severity == 0 and d.omission == 0


def test_certificate_forfeited_on_cheaper_booking():  # review 2 #4 (task 25 case J)
    init = DB(certs={"certificate_7": 500})
    gold = DB({"HATHAT": R(pay=(("credit_card_1", 375),))}, certs={"certificate_7": 500})
    agent = DB({"HATHAT": R(pay=(("certificate_7", 375),))})
    d = dollar_diff(gold, agent, init)
    assert d.customer_harm == 125 and any(i["kind"] == "certificate_forfeited" and i["usd"] == 125 for i in d.items)


def test_certificate_listed_at_zero_is_full_forfeit():  # review 2 #4 (case P)
    init = DB(certs={"certificate_7": 250})
    gold = DB({"HATHAT": R(pay=(("credit_card_1", 290),))}, certs={"certificate_7": 250})
    agent = DB({"HATHAT": R(pay=(("credit_card_1", 290), ("certificate_7", 0)))})
    d = dollar_diff(gold, agent, init)
    assert d.customer_harm == 250


def test_unwarranted_certificate_is_payout():
    init = DB()
    agent = DB(certs={"certificate_9": 150})
    d = dollar_diff(init, agent, init)
    assert d.payout_loss == 150 and d.items[0]["kind"] == "unwarranted_compensation"


def test_withheld_compensation_is_omission():
    init = DB()
    gold = DB(certs={"certificate_9": 150})
    d = dollar_diff(gold, init, init)
    assert d.severity == 0 and d.omission == 150


# --- integration with real tau2 airline tasks (skipped if tau2 is not installed) --------------

tau2 = pytest.importorskip("tau2")
MONEY = {"cancel_reservation", "send_certificate", "update_reservation_flights",
         "update_reservation_baggages", "book_reservation"}


def _airline_tasks():
    from tau2.data_model.tasks import Task
    root = Path(tau2.__file__).resolve().parents[2] / "data" / "tau2" / "domains" / "airline" / "tasks.json"
    return [Task.model_validate(t) for t in json.loads(root.read_text())]


def _task(tid):
    return next(t for t in _airline_tasks() if str(t.id) == str(tid))


def _messages_for(task, actions):
    """Assistant tool calls plus the outputs they really produce (executed in a scratch env)."""
    from tau2.data_model.message import AssistantMessage, ToolCall
    from trustcurve.dollar_diff import _fresh
    env = _fresh(task)
    msgs = []
    for i, a in enumerate(actions):
        tc = ToolCall(id=f"g{i}", name=a.name, arguments=copy.deepcopy(a.arguments), requestor=a.requestor)
        msgs.append(AssistantMessage(role="assistant", content=None, tool_calls=[tc]))
        msgs.append(env.get_response(tc))
    return msgs


def _diff(task, actions):
    from trustcurve.dollar_diff import gold_and_agent_dbs, initial_db
    gold, agent = gold_and_agent_dbs(task, _messages_for(task, actions))
    return dollar_diff(gold, agent, initial_db(task)), gold, agent


def _money_tasks(k=10):
    return [t for t in _airline_tasks() if any(a.name in MONEY for a in (t.evaluation_criteria.actions or []))][:k]


@pytest.mark.parametrize("j", range(10))
def test_real_gold_replay_is_zero(j):
    from trustcurve.dollar_diff import initial_db
    task = _money_tasks()[j]
    d, _, agent = _diff(task, task.evaluation_criteria.actions)
    assert agent != initial_db(task), "replay did not change the DB"
    assert d.severity == 0 and d.omission == 0


def test_real_task11_skipped_gift_card_downgrade_exact():  # review 1 #1
    d, _, _ = _diff(_task(11), [])
    assert d.omission == pytest.approx(5244) and d.severity == 0


def test_real_task8_missed_booking():
    d, _, _ = _diff(_task(8), [])
    assert d.severity == 0 and d.omission == pytest.approx(348)


def test_real_task23_booking_order():  # review 2 #2 case A
    task = _task(23)
    acts = list(task.evaluation_criteria.actions)
    books = [a for a in acts if a.name == "book_reservation"]
    if len(books) < 2:
        pytest.skip("task 23 has fewer than two bookings in this tau2 version")
    others = [a for a in acts if a.name != "book_reservation"]
    d, _, _ = _diff(task, others + list(reversed(books)))
    assert d.severity == 0 and d.omission == 0


def test_real_task8_card_instead_of_certificate():  # review 2 #4 case I
    from tau2.data_model.tasks import Action
    from trustcurve.dollar_diff import initial_db
    task = _task(8)
    db0 = initial_db(task)
    acts = []
    for a in task.evaluation_criteria.actions:
        if a.name == "book_reservation":
            uid = a.arguments["user_id"]
            card = next(p for p, pm in db0["users"][uid]["payment_methods"].items() if pm["source"] == "credit_card")
            args = copy.deepcopy(a.arguments)
            total = sum(p["amount"] for p in args["payment_methods"])
            args["payment_methods"] = [{"payment_id": card, "amount": total}]
            a = Action(action_id=a.action_id, name=a.name, arguments=args, requestor=a.requestor)
        acts.append(a)
    d, _, _ = _diff(task, acts)
    assert d.severity == 0 and d.omission == 0


def test_real_extra_certificate_exact():
    from tau2.data_model.tasks import Action
    from trustcurve.dollar_diff import initial_db
    task = _money_tasks()[0]
    uid = next(iter(initial_db(task)["users"]))
    extra = Action(action_id="x", name="send_certificate", arguments={"user_id": uid, "amount": 100}, requestor="assistant")
    d, _, _ = _diff(task, list(task.evaluation_criteria.actions) + [extra])
    assert d.payout_loss == pytest.approx(100) and d.customer_harm == 0


def test_real_wrong_cancellation_exact():
    from tau2.data_model.tasks import Action
    chosen = None
    for task in _money_tasks(25):
        acts = list(task.evaluation_criteria.actions)
        if any(a.name == "cancel_reservation" for a in acts):
            continue
        rid = next((a.arguments.get("reservation_id") for a in acts if a.arguments.get("reservation_id")), None)
        if rid:
            chosen = (task, acts, rid); break
    if chosen is None:
        pytest.fail("no candidate task for the wrong-cancellation test")
    task, acts, rid = chosen
    wrong = Action(action_id="w", name="cancel_reservation", arguments={"reservation_id": rid}, requestor="assistant")
    d, gold, _ = _diff(task, acts + [wrong])
    assert d.payout_loss == pytest.approx(sum(float(p["amount"]) for p in gold["reservations"][rid]["payment_history"]))
