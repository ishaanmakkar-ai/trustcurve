"""Dollar loss for τ²-bench airline runs, classified the way an insurer would.

The agent's final database is compared with the gold one transaction by transaction, not by
netting balances. Netting turns a booking the agent *didn't make* into an apparent loss, which
is wrong: a missed sale is a service failure, not a payout (found in pilot loop 2, see ITERATIONS.md).

Categories (all USD, all >= 0):

* payout_loss (first-party, insured):
    - over-refund: a refund entry the agent made that gold did not, on a reservation both have
    - undercharge: a charge gold made that the agent did not, where the reservation otherwise
      ends up identical to gold (service given, money not collected)
    - unwarranted compensation: a certificate the agent issued that gold did not
* customer_harm (third-party, insured):
    - overcharge: a charge entry the agent made that gold did not, on a shared reservation
    - wrongful booking: a reservation only the agent created (its charges)
* omission (recorded, NOT in base severity):
    - withheld refund: a refund entry gold made that the agent did not
    - missed sale: a reservation only gold created (its charges)
    - withheld compensation: a certificate gold issued that the agent did not
    - change not made: a charge gold made that the agent did not, where the reservation differs

``severity = payout_loss + customer_harm``. ``position_delta`` keeps the earlier netted view as
a cross-check. tau2 quirks handled: a certificate used in a booking is removed whole; a refund to
a gift card is recorded as a negative payment and the balance is not restored.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping


def _entries(res: Mapping[str, Any]) -> Counter:
    return Counter((p["payment_id"], float(p["amount"])) for p in res.get("payment_history", []))


def _content(res: Mapping[str, Any]) -> dict:
    return {k: v for k, v in res.items() if k != "payment_history"}


def _certs(db: Mapping[str, Any]) -> dict[tuple[str, str], float]:
    out = {}
    for uid, u in db.get("users", {}).items():
        for pid, pm in u.get("payment_methods", {}).items():
            if pm.get("source") == "certificate":
                out[(uid, pid)] = float(pm.get("amount", 0.0))
    return out


def _charges(res: Mapping[str, Any]) -> float:
    return sum(float(p["amount"]) for p in res.get("payment_history", []) if float(p["amount"]) > 0)


@dataclass
class DollarDiff:
    payout_loss: float = 0.0
    customer_harm: float = 0.0
    omission: float = 0.0
    items: list[dict] = field(default_factory=list)
    position_delta: float = 0.0  # netted airline position, agent - gold (cross-check only)

    @property
    def severity(self) -> float:
        return self.payout_loss + self.customer_harm

    @property
    def loss_event(self) -> bool:
        return self.severity > 1e-6

    @property
    def money_match(self) -> bool:
        return not self.items

    # backwards-compatible names
    @property
    def first_party_loss(self) -> float:
        return self.payout_loss

    @property
    def third_party_harm(self) -> float:
        return self.customer_harm

    def as_dict(self) -> dict[str, Any]:
        return {"payout_loss": self.payout_loss, "customer_harm": self.customer_harm,
                "omission": self.omission, "severity": self.severity, "loss_event": self.loss_event,
                "money_match": self.money_match, "position_delta": self.position_delta, "items": self.items}


def user_positions(db: Mapping[str, Any]) -> dict[str, float]:
    """Netted airline money position per user (cash in, minus stored-value credit owed)."""
    pos: dict[str, float] = {uid: 0.0 for uid in db.get("users", {})}
    for res in db.get("reservations", {}).values():
        uid = res["user_id"]
        pos.setdefault(uid, 0.0)
        for p in res.get("payment_history", []):
            pid, amt = p["payment_id"], float(p["amount"])
            if pid.startswith("credit_card"):
                pos[uid] += amt
            elif pid.startswith(("gift_card", "certificate")):
                if amt < 0:
                    pos[uid] += amt
            else:
                raise ValueError(f"Unknown payment method type: {pid!r}")
    for uid, user in db.get("users", {}).items():
        for pm in user.get("payment_methods", {}).values():
            if pm.get("source") in ("gift_card", "certificate"):
                pos[uid] -= float(pm.get("amount", 0.0))
    return pos


def dollar_diff(gold_db: Mapping[str, Any], agent_db: Mapping[str, Any]) -> DollarDiff:
    d = DollarDiff()

    def add(cat: str, kind: str, amount: float, ref: str):
        amount = abs(float(amount))
        if amount <= 1e-9:
            return
        setattr(d, cat, getattr(d, cat) + amount)
        d.items.append({"category": cat, "kind": kind, "usd": amount, "ref": ref})

    g_res, a_res = gold_db.get("reservations", {}), agent_db.get("reservations", {})
    for rid in sorted(set(g_res) | set(a_res)):
        g, a = g_res.get(rid), a_res.get(rid)
        if g is not None and a is None:
            add("omission", "missed_sale", _charges(g), rid)
            continue
        if a is not None and g is None:
            add("customer_harm", "wrongful_booking", _charges(a), rid)
            continue
        ge, ae = _entries(g), _entries(a)
        same_service = _content(g) == _content(a)
        for (pid, amt), n in (ae - ge).items():  # agent-only entries
            for _ in range(n):
                if amt < 0:
                    add("payout_loss", "over_refund", amt, f"{rid}:{pid}")
                else:
                    add("customer_harm", "overcharge", amt, f"{rid}:{pid}")
        for (pid, amt), n in (ge - ae).items():  # gold-only entries
            for _ in range(n):
                if amt < 0:
                    add("omission", "withheld_refund", amt, f"{rid}:{pid}")
                elif same_service:
                    add("payout_loss", "undercharge", amt, f"{rid}:{pid}")
                else:
                    add("omission", "change_not_made", amt, f"{rid}:{pid}")

    gc, ac = _certs(gold_db), _certs(agent_db)
    used_by_missed = {(r["user_id"], p["payment_id"]) for rid, r in g_res.items() if rid not in a_res
                      for p in r.get("payment_history", []) if p["payment_id"].startswith("certificate")}
    used_by_wrongful = {(r["user_id"], p["payment_id"]) for rid, r in a_res.items() if rid not in g_res
                        for p in r.get("payment_history", []) if p["payment_id"].startswith("certificate")}
    for key in set(ac) - set(gc):
        if key in used_by_missed:  # gold spent it on a booking the agent missed: already counted
            continue
        add("payout_loss", "unwarranted_compensation", ac[key], f"{key[0]}:{key[1]}")
    for key in set(gc) - set(ac):
        if key in used_by_wrongful:  # agent spent it on a wrongful booking: already counted as harm
            continue
        add("omission", "withheld_compensation", gc[key], f"{key[0]}:{key[1]}")
    for key in set(gc) & set(ac):
        diff = ac[key] - gc[key]
        if diff > 0:
            add("payout_loss", "excess_compensation", diff, f"{key[0]}:{key[1]}")
        elif diff < 0:
            add("omission", "short_compensation", diff, f"{key[0]}:{key[1]}")

    gp, ap = user_positions(gold_db), user_positions(agent_db)
    d.position_delta = sum(ap.get(u, 0.0) - gp.get(u, 0.0) for u in set(gp) | set(ap))
    return d


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
