"""Tests for the dollar diff. Each case is built so that a wrong implementation fails it."""

import copy
import json
import os
from pathlib import Path

import pytest

from trustcurve.dollar_diff import dollar_diff, user_positions


def base_db():
    return {
        "users": {
            "u1": {"payment_methods": {
                "credit_card_1": {"source": "credit_card", "id": "credit_card_1"},
                "gift_card_1": {"source": "gift_card", "id": "gift_card_1", "amount": 200.0},
            }},
            "u2": {"payment_methods": {"credit_card_2": {"source": "credit_card", "id": "credit_card_2"}}},
        },
        "reservations": {
            "R1": {"user_id": "u1", "payment_history": [{"payment_id": "credit_card_1", "amount": 500}]},
            "R2": {"user_id": "u2", "payment_history": [{"payment_id": "credit_card_2", "amount": 300}]},
        },
    }


def test_identical_dbs_have_zero_loss():
    d = dollar_diff(base_db(), base_db())
    assert d.money_match and d.severity == 0 and d.delta == 0


def test_known_wrong_double_refund_is_first_party_loss():
    gold = base_db()
    gold["reservations"]["R1"]["payment_history"].append({"payment_id": "credit_card_1", "amount": -500})
    agent = copy.deepcopy(gold)
    agent["reservations"]["R1"]["payment_history"].append({"payment_id": "credit_card_1", "amount": -500})
    d = dollar_diff(gold, agent)
    assert d.first_party_loss == 500 and d.third_party_harm == 0 and d.delta == -500


def test_unwarranted_certificate_is_loss():
    gold = base_db()
    agent = copy.deepcopy(gold)
    agent["users"]["u2"]["payment_methods"]["certificate_9"] = {"source": "certificate", "id": "certificate_9", "amount": 150.0}
    d = dollar_diff(gold, agent)
    assert d.first_party_loss == 150 and d.per_user == {"u2": -150}


def test_overcharge_is_third_party_harm():
    gold = base_db()
    agent = copy.deepcopy(gold)
    agent["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": 120})
    d = dollar_diff(gold, agent)
    assert d.third_party_harm == 120 and d.first_party_loss == 0


def test_offsetting_errors_across_users_are_not_netted():
    gold = base_db()
    agent = copy.deepcopy(gold)
    agent["reservations"]["R1"]["payment_history"].append({"payment_id": "credit_card_1", "amount": -100})
    agent["reservations"]["R2"]["payment_history"].append({"payment_id": "credit_card_2", "amount": 100})
    d = dollar_diff(gold, agent)
    assert d.delta == 0 and d.severity == 200 and not d.money_match


def test_gift_card_refund_counts_as_credit_owed():
    # tau2 cancel appends a negative gift-card payment but does not restore the balance.
    gold = base_db()
    gold["reservations"]["R3"] = {"user_id": "u1", "payment_history": [{"payment_id": "gift_card_1", "amount": 80}]}
    gold["users"]["u1"]["payment_methods"]["gift_card_1"]["amount"] = 120.0
    agent = copy.deepcopy(gold)
    agent["reservations"]["R3"]["payment_history"].append({"payment_id": "gift_card_1", "amount": -80})
    d = dollar_diff(gold, agent)
    assert d.first_party_loss == 80


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
    assert dollar_diff(gold, agent).money_match


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


def test_real_task_wrong_cancellation_is_detected():
    from tau2.data_model.tasks import Action
    from trustcurve.dollar_diff import gold_and_agent_dbs
    for task in _money_tasks(25):
        acts = list(task.evaluation_criteria.actions)
        if not any(a.name == "cancel_reservation" for a in acts):
            res = next((a.arguments.get("reservation_id") for a in acts if a.arguments.get("reservation_id")), None)
            if res:
                break
    wrong = Action(action_id="w", name="cancel_reservation", arguments={"reservation_id": res}, requestor="assistant")
    gold, agent = gold_and_agent_dbs(task, _messages_for(task, acts + [wrong]))
    d = dollar_diff(gold, agent)
    assert d.first_party_loss > 0
