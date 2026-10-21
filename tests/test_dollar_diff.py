"""Tests for the dollar diff. Each case is built so that a wrong implementation fails it."""

import copy
import json
from pathlib import Path

import pytest

from trustcurve.dollar_diff import dollar_diff, user_positions


def base_db():
    return {
        "users": {
            "u1": {"payment_methods": {
                "credit_card_1": {"source": "credit_card", "id": "credit_card_1"},
                "gift_card_1": {"source": "gift_card", "id": "gift_card_1", "amount": 200.0},
                "certificate_7": {"source": "certificate", "id": "certificate_7", "amount": 300.0},
            }},
            "u2": {"payment_methods": {"credit_card_2": {"source": "credit_card", "id": "credit_card_2"}}},
        },
        "reservations": {
            "R1": {"user_id": "u1", "cabin": "economy", "payment_history": [{"payment_id": "credit_card_1", "amount": 500}]},
            "R2": {"user_id": "u2", "cabin": "economy", "payment_history": [{"payment_id": "credit_card_2", "amount": 300}]},
        },
    }


def test_identical_dbs_have_zero_loss():
    d = dollar_diff(base_db(), base_db())
    assert d.money_match and d.severity == 0 and d.omission == 0


def test_wrongful_cancellation_is_over_refund_payout():
    gold = base_db(); agent = copy.deepcopy(gold)
    agent["reservations"]["R1"]["payment_history"].append({"payment_id": "credit_card_1", "amount": -500})
    d = dollar_diff(gold, agent)
    assert d.payout_loss == 500 and d.customer_harm == 0 and d.omission == 0


def test_unwarranted_certificate_is_payout():
    gold = base_db(); agent = copy.deepcopy(gold)
    agent["users"]["u2"]["payment_methods"]["certificate_9"] = {"source": "certificate", "id": "certificate_9", "amount": 150.0}
    d = dollar_diff(gold, agent)
    assert d.payout_loss == 150 and d.items[0]["kind"] == "unwarranted_compensation"


def test_overcharge_is_customer_harm():
    gold = base_db(); agent = copy.deepcopy(gold)
    agent["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": 120})
    d = dollar_diff(gold, agent)
    assert d.customer_harm == 120 and d.payout_loss == 0


def test_offsetting_errors_are_not_netted():
    gold = base_db(); agent = copy.deepcopy(gold)
    agent["reservations"]["R1"]["payment_history"].append({"payment_id": "credit_card_1", "amount": -100})
    agent["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": 100})
    d = dollar_diff(gold, agent)
    assert d.payout_loss == 100 and d.customer_harm == 100 and d.severity == 200


def test_missed_booking_is_omission_not_loss():
    # Loop-2 bug: gold books R3 with a certificate (removed whole); agent books nothing.
    gold = base_db(); agent = copy.deepcopy(gold)
    gold["reservations"]["R3"] = {"user_id": "u1", "cabin": "economy",
                                  "payment_history": [{"payment_id": "certificate_7", "amount": 250}]}
    del gold["users"]["u1"]["payment_methods"]["certificate_7"]
    d = dollar_diff(gold, agent)
    assert d.severity == 0 and d.omission == 250 and d.items[0]["kind"] == "missed_sale"


def test_withheld_refund_is_omission_not_loss():
    gold = base_db(); agent = copy.deepcopy(gold)
    gold["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": -300})
    d = dollar_diff(gold, agent)
    assert d.severity == 0 and d.omission == 300


def test_wrongful_booking_is_customer_harm():
    gold = base_db(); agent = copy.deepcopy(gold)
    agent["reservations"]["R9"] = {"user_id": "u2", "cabin": "economy",
                                   "payment_history": [{"payment_id": "credit_card_2", "amount": 410}]}
    d = dollar_diff(gold, agent)
    assert d.customer_harm == 410 and d.items[0]["kind"] == "wrongful_booking"


def test_upgrade_given_without_charge_is_undercharge():
    gold = base_db(); agent = copy.deepcopy(gold)
    for db in (gold, agent):
        db["reservations"]["R2"]["cabin"] = "business"
    gold["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": 200})
    d = dollar_diff(gold, agent)
    assert d.payout_loss == 200 and d.items[0]["kind"] == "undercharge"


def test_change_not_made_is_omission():
    gold = base_db(); agent = copy.deepcopy(gold)
    gold["reservations"]["R2"]["cabin"] = "business"
    gold["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": 200})
    d = dollar_diff(gold, agent)
    assert d.severity == 0 and d.omission == 200


def test_gift_card_refund_counted_once():
    # Reviewer finding #1: a gift-card downgrade restores the balance AND appends a negative entry.
    gold = base_db(); agent = copy.deepcopy(gold)
    agent["reservations"]["R1"]["payment_history"].append({"payment_id": "gift_card_1", "amount": -80})
    agent["users"]["u1"]["payment_methods"]["gift_card_1"]["amount"] = 280.0
    d = dollar_diff(gold, agent)
    assert d.payout_loss == 80


def test_unknown_payment_type_raises():
    db = base_db()
    db["reservations"]["R1"]["payment_history"].append({"payment_id": "paypal_1", "amount": 10})
    with pytest.raises(ValueError):
        user_positions(db)


# --- integration with real tau2 airline tasks (skipped if tau2 is not installed) --------------

tau2 = pytest.importorskip("tau2")


def _airline_tasks():
    from tau2.data_model.tasks import Task
    root = Path(tau2.__file__).resolve().parents[2] / "data" / "tau2" / "domains" / "airline" / "tasks.json"
    return [Task.model_validate(t) for t in json.loads(root.read_text())]


def _messages_for(task, actions):
    """Assistant tool calls + the tool outputs they really produce (executed in a scratch env)."""
    from copy import deepcopy
    from tau2.data_model.message import AssistantMessage, ToolCall
    from tau2.registry import registry
    env = registry.get_env_constructor("airline")()
    init = task.initial_state
    env.set_state(initialization_data=init.initialization_data if init else None,
                  initialization_actions=init.initialization_actions if init else None,
                  message_history=(init.message_history if init and init.message_history else []) or [])
    msgs = []
    for i, a in enumerate(actions):
        tc = ToolCall(id=f"g{i}", name=a.name, arguments=deepcopy(a.arguments), requestor=a.requestor)
        msgs.append(AssistantMessage(role="assistant", content=None, tool_calls=[tc]))
        msgs.append(env.get_response(tc))
    return msgs


MONEY = {"cancel_reservation", "send_certificate", "update_reservation_flights",
         "update_reservation_baggages", "book_reservation"}


def _money_tasks(k=5):
    ts = _airline_tasks()
    return [t for t in ts if any(a.name in MONEY for a in (t.evaluation_criteria.actions or []))][:k]


@pytest.mark.parametrize("j", range(5))
def test_real_money_task_gold_replay_has_zero_loss(j):
    from trustcurve.dollar_diff import gold_and_agent_dbs
    task = _money_tasks()[j]
    gold, agent = gold_and_agent_dbs(task, _messages_for(task, task.evaluation_criteria.actions))
    # the replay must actually move money relative to the initial DB, or the test is vacuous
    from tau2.registry import registry
    from trustcurve.dollar_diff import user_positions
    initial = registry.get_env_constructor("airline")().tools.db.model_dump(mode="json")
    assert agent != initial, "replay did not change the DB"
    d = dollar_diff(gold, agent)
    assert d.money_match and d.severity == 0 and d.omission == 0
    # and the same task with NO agent actions must differ from gold when gold moves money
    gold2, none = gold_and_agent_dbs(task, [])
    moved = user_positions(gold2) != user_positions(initial)
    if moved:
        assert not dollar_diff(gold2, none).money_match


def test_most_money_tasks_really_move_money():
    """Guard against a vacuous suite: free-bag updates etc. move no money, but most should."""
    from tau2.registry import registry
    from trustcurve.dollar_diff import gold_and_agent_dbs, user_positions
    initial = user_positions(registry.get_env_constructor("airline")().tools.db.model_dump(mode="json"))
    moved = 0
    for task in _money_tasks(10):
        _, agent = gold_and_agent_dbs(task, _messages_for(task, task.evaluation_criteria.actions))
        moved += user_positions(agent) != initial
    assert moved >= 7


def test_real_task_extra_certificate_is_detected():
    from tau2.data_model.tasks import Action
    from trustcurve.dollar_diff import gold_and_agent_dbs
    task = _money_tasks()[0]
    uid = next(a.arguments["user_id"] for a in task.evaluation_criteria.actions if "user_id" in a.arguments) \
        if any("user_id" in a.arguments for a in task.evaluation_criteria.actions) else None
    if uid is None:
        uid = next(iter(json.loads((Path(tau2.__file__).resolve().parents[2] / "data/tau2/domains/airline/db.json").read_text())["users"]))
    extra = Action(action_id="x", name="send_certificate", arguments={"user_id": uid, "amount": 100}, requestor="assistant")
    gold, agent = gold_and_agent_dbs(task, _messages_for(task, list(task.evaluation_criteria.actions) + [extra]))
    d = dollar_diff(gold, agent)
    assert d.first_party_loss == 100 and d.third_party_harm == 0


def test_real_task_wrong_cancellation_is_exact():
    from tau2.data_model.tasks import Action
    from trustcurve.dollar_diff import gold_and_agent_dbs
    chosen = None
    for task in _money_tasks(25):
        acts = list(task.evaluation_criteria.actions)
        if any(a.name == "cancel_reservation" for a in acts):
            continue
        res = next((a.arguments.get("reservation_id") for a in acts if a.arguments.get("reservation_id")), None)
        if res:
            chosen = (task, acts, res); break
    if chosen is None:
        pytest.fail("no candidate task found for the wrong-cancellation test")
    task, acts, res = chosen
    wrong = Action(action_id="w", name="cancel_reservation", arguments={"reservation_id": res}, requestor="assistant")
    gold, agent = gold_and_agent_dbs(task, _messages_for(task, acts + [wrong]))
    expected = sum(float(p["amount"]) for p in gold["reservations"][res]["payment_history"])
    d = dollar_diff(gold, agent)
    assert d.payout_loss == pytest.approx(expected) and d.customer_harm == 0


def _task(tid):
    return next(t for t in _airline_tasks() if str(t.id) == str(tid))


def test_task11_skipped_gift_card_downgrade_is_exact_omission():
    """Reviewer finding #1 regression: gold refunds $5,244 to a gift card; agent does nothing."""
    from trustcurve.dollar_diff import gold_and_agent_dbs
    task = _task(11)
    gold, agent = gold_and_agent_dbs(task, [])
    d = dollar_diff(gold, agent)
    refunds = [i for i in d.items if i["kind"] == "withheld_refund"]
    assert sum(i["usd"] for i in refunds) == pytest.approx(5244) and d.severity == 0


def test_task8_missed_booking_is_omission():
    from trustcurve.dollar_diff import gold_and_agent_dbs
    gold, agent = gold_and_agent_dbs(_task(8), [])
    d = dollar_diff(gold, agent)
    assert d.severity == 0 and d.omission > 0 and all(i["category"] == "omission" for i in d.items)
