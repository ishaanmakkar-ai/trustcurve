"""Dollar loss for τ²-bench airline runs: compare the agent's final database with the gold one.

Accounting model (airline's point of view, money only; flights/seats/bags are not valued):

* cash      = sum of payment_history amounts paid by credit card (refunds are negative entries)
* liability = outstanding gift-card and certificate balances
              + refunds recorded against gift cards / certificates
                (tau2 appends a negative payment on refund but never restores the balance,
                 so the refund is credit the airline still owes)
* position  = cash - liability

For a run, ``delta = position(agent) - position(gold)``:

* delta < 0  -> the airline is worse off than the correct outcome (over-refund, extra
                compensation, under-charge): a first-party loss of ``-delta`` dollars.
* delta > 0  -> the customer was charged more than they should have been: third-party
                harm of ``delta`` dollars.

Both directions are potential claims, so ``severity = |delta|``. Per-user positions are also
returned so that offsetting errors across users are not hidden by netting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

CREDIT_PREFIXES = ("credit_card",)
STORED_VALUE_PREFIXES = ("gift_card", "certificate")


def _kind(payment_id: str) -> str:
    if payment_id.startswith(CREDIT_PREFIXES):
        return "cash"
    if payment_id.startswith(STORED_VALUE_PREFIXES):
        return "stored"
    raise ValueError(f"Unknown payment method type: {payment_id!r}")


def user_positions(db: Mapping[str, Any]) -> dict[str, float]:
    """Airline's money position per user ID for an airline DB given as a plain dict."""
    pos: dict[str, float] = {uid: 0.0 for uid in db.get("users", {})}
    for res in db.get("reservations", {}).values():
        uid = res["user_id"]
        pos.setdefault(uid, 0.0)
        for p in res.get("payment_history", []):
            amt = float(p["amount"])
            if _kind(p["payment_id"]) == "cash":
                pos[uid] += amt
            elif amt < 0:  # refund to stored value: credit owed back to the customer
                pos[uid] += amt
    for uid, user in db.get("users", {}).items():
        for pm in user.get("payment_methods", {}).values():
            if pm.get("source") in ("gift_card", "certificate"):
                pos[uid] -= float(pm.get("amount", 0.0))
    return pos


@dataclass
class DollarDiff:
    delta: float  # agent position minus gold position (airline view)
    first_party_loss: float  # airline worse off than gold
    third_party_harm: float  # customer overcharged relative to gold
    severity: float  # |delta| summed per user (no netting across users)
    per_user: dict[str, float] = field(default_factory=dict)  # non-zero user deltas only
    money_match: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "delta": self.delta,
            "first_party_loss": self.first_party_loss,
            "third_party_harm": self.third_party_harm,
            "severity": self.severity,
            "per_user": self.per_user,
            "money_match": self.money_match,
        }


def dollar_diff(gold_db: Mapping[str, Any], agent_db: Mapping[str, Any], tol: float = 1e-6) -> DollarDiff:
    g = user_positions(gold_db)
    a = user_positions(agent_db)
    per_user = {}
    for uid in set(g) | set(a):
        d = a.get(uid, 0.0) - g.get(uid, 0.0)
        if abs(d) > tol:
            per_user[uid] = d
    first = sum(-d for d in per_user.values() if d < 0)
    third = sum(d for d in per_user.values() if d > 0)
    delta = sum(per_user.values())
    return DollarDiff(
        delta=delta,
        first_party_loss=first,
        third_party_harm=third,
        severity=first + third,
        per_user=per_user,
        money_match=not per_user,
    )


# --- tau2 integration -------------------------------------------------------------------------

def _db_dict(env) -> dict[str, Any]:
    return env.tools.db.model_dump(mode="json")


def gold_and_agent_dbs(task, messages, domain: str = "airline", env_kwargs: dict | None = None):
    """Rebuild the gold and agent end-state DBs exactly as tau2's EnvironmentEvaluator does."""
    from copy import deepcopy

    from tau2.registry import registry

    ctor = registry.get_env_constructor(domain)
    env_kwargs = env_kwargs or {}
    init = task.initial_state
    init_data = init.initialization_data if init else None
    init_actions = init.initialization_actions if init else None
    history = (init.message_history if init and init.message_history else []) or []

    agent_env = ctor(**deepcopy(env_kwargs))
    agent_env.set_state(initialization_data=init_data, initialization_actions=init_actions,
                        message_history=list(messages), strict=True)
    gold_env = ctor(**deepcopy(env_kwargs))
    gold_env.set_state(initialization_data=init_data, initialization_actions=init_actions,
                       message_history=history, strict=True)
    for action in (task.evaluation_criteria.actions or []):
        try:
            gold_env.make_tool_call(tool_name=action.name, requestor=action.requestor, **action.arguments)
        except Exception:  # mirror tau2: a failing gold action is skipped
            pass
    return _db_dict(gold_env), _db_dict(agent_env)
