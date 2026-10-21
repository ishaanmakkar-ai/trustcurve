"""Dollar loss for τ²-bench airline runs, classified the way an insurer would (v3).

v1 netted balances (scored missed bookings as payouts). v2 matched payment entries exactly and
paired reservations by ID (scored a different route or booking order to the same correct end
state as loss). v3 (review 2):

* Reservations are paired by **content** (user, route, flights+dates, cabin, passengers), with
  pre-existing reservations (present in the initial DB) paired by ID.
* Money is compared as the **net** charge per paired reservation, so +X/-X pairs, split vs.
  combined changes and refunds to a different card all net out.
* Who changed what is decided against the **initial** reservation:
    - agent changed it and gold didn't, or both changed it differently -> commission
      (net agent < gold -> payout_loss; net agent > gold -> customer_harm);
    - gold changed it and the agent didn't -> omission (|net diff|);
    - same customer-facing service, different net -> undercharge (payout) or overcharge (harm).
* Unpaired new reservations: gold-only -> omission (missed sale, net charge); agent-only ->
  customer_harm (wrongful booking, net charge; a booking the agent cancelled again nets to $0).
* Stored value: a certificate the agent consumed that gold did not -> customer_harm equal to the
  forfeited value (face - amount applied); certificates created only by the agent -> payout
  (unwarranted compensation); created only by gold -> omission. Payment-method-only differences
  with equal net are recorded at $0.

``severity = payout_loss + customer_harm``; omissions are reported separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

BAG_FEE = 50


def _net(res) -> float:
    return sum(float(p["amount"]) for p in res.get("payment_history", []))


def _pax(res):
    return tuple(sorted((p["first_name"].casefold(), p["last_name"].casefold(), p["dob"]) for p in res.get("passengers", [])))


def _route_key(res):
    return (res.get("user_id"), res.get("origin"), res.get("destination"), res.get("flight_type"),
            tuple(sorted((f["flight_number"], f["date"]) for f in res.get("flights", []))), _pax(res))


def _service(res):
    """Customer-facing service (what the customer gets), excluding how it was paid."""
    return _route_key(res) + (res.get("cabin"), res.get("total_baggages"), res.get("insurance"), res.get("status"))


def _certs(db) -> dict[tuple[str, str], float]:
    return {(uid, pid): float(pm.get("amount", 0.0))
            for uid, u in db.get("users", {}).items()
            for pid, pm in u.get("payment_methods", {}).items() if pm.get("source") == "certificate"}


@dataclass
class DollarDiff:
    payout_loss: float = 0.0
    customer_harm: float = 0.0
    omission: float = 0.0
    items: list[dict] = field(default_factory=list)

    @property
    def severity(self) -> float:
        return self.payout_loss + self.customer_harm

    @property
    def loss_event(self) -> bool:
        return self.severity > 1e-6

    @property
    def money_match(self) -> bool:
        return not any(i["usd"] > 1e-9 for i in self.items)

    first_party_loss = property(lambda self: self.payout_loss)
    third_party_harm = property(lambda self: self.customer_harm)

    def as_dict(self):
        return {"payout_loss": self.payout_loss, "customer_harm": self.customer_harm, "omission": self.omission,
                "severity": self.severity, "loss_event": self.loss_event, "items": self.items}


def _pair(gold_new: dict, agent_new: dict):
    """Pair new reservations by full service, then by route; return pairs and leftovers."""
    pairs, g_left, a_left = [], dict(gold_new), dict(agent_new)
    for keyf in (_service, _route_key):
        for gid in sorted(list(g_left)):
            gk = keyf(g_left[gid])
            match = next((aid for aid in sorted(a_left) if keyf(a_left[aid]) == gk), None)
            if match is not None:
                pairs.append((g_left.pop(gid), a_left.pop(match), f"{gid}~{match}"))
    return pairs, g_left, a_left


def dollar_diff(gold_db: Mapping[str, Any], agent_db: Mapping[str, Any],
                initial_db: Mapping[str, Any] | None = None) -> DollarDiff:
    d = DollarDiff()

    def add(cat, kind, usd, ref):
        usd = abs(float(usd))
        if usd > 1e-9 or kind == "payment_method_mismatch":
            if cat:
                setattr(d, cat, getattr(d, cat) + usd)
            d.items.append({"category": cat or "info", "kind": kind, "usd": usd, "ref": ref})

    g_res, a_res = gold_db.get("reservations", {}), agent_db.get("reservations", {})
    i_res = (initial_db or {}).get("reservations")
    existing = set(i_res) if i_res is not None else set(g_res) & set(a_res)
    init = i_res or {}

    pairs = [(g_res[r], a_res[r], r, init.get(r)) for r in sorted(existing) if r in g_res and r in a_res]
    new_pairs, g_left, a_left = _pair({k: v for k, v in g_res.items() if k not in existing},
                                      {k: v for k, v in a_res.items() if k not in existing})
    pairs += [(g, a, ref, None) for g, a, ref in new_pairs]

    for g, a, ref, i in pairs:
        diff = _net(a) - _net(g)
        same = _service(g) == _service(a)
        if same:
            if abs(diff) < 1e-9:
                if sorted(p["payment_id"] for p in g.get("payment_history", [])) != sorted(p["payment_id"] for p in a.get("payment_history", [])):
                    add(None, "payment_method_mismatch", 0, ref)
                continue
            if diff < 0:
                add("payout_loss", "undercharge" if a.get("status") != "cancelled" else "over_refund", diff, ref)
            else:
                add("customer_harm", "overcharge", diff, ref)
            continue
        agent_changed = i is None or _service(a) != _service(i) or abs(_net(a) - _net(i)) > 1e-9
        gold_changed = i is None or _service(g) != _service(i) or abs(_net(g) - _net(i)) > 1e-9
        if gold_changed and not agent_changed:
            add("omission", "withheld_refund" if g.get("status") == "cancelled" else "change_not_made", diff, ref)
        elif abs(diff) < 1e-9:
            add(None, "service_mismatch_no_money", 0, ref)
        elif diff < 0:
            kind = "over_refund" if a.get("status") == "cancelled" and g.get("status") != "cancelled" else "wrongful_change_refund"
            add("payout_loss", kind, diff, ref)
        else:
            add("customer_harm", "wrongful_change_charge", diff, ref)

    for rid, g in sorted(g_left.items()):
        add("omission", "missed_sale", _net(g), rid)
    for rid, a in sorted(a_left.items()):
        add("customer_harm", "wrongful_booking", _net(a), rid)

    # stored value
    gc, ac = _certs(gold_db), _certs(agent_db)
    ic = _certs(initial_db) if initial_db is not None else {k: v for k, v in gc.items() if k in ac}
    applied_by_agent: dict[str, float] = {}
    for r in a_res.values():
        for p in r.get("payment_history", []):
            if p["payment_id"].startswith("certificate") and float(p["amount"]) > 0:
                applied_by_agent[p["payment_id"]] = applied_by_agent.get(p["payment_id"], 0.0) + float(p["amount"])
    for key, face in ic.items():
        if key in gc and key not in ac:  # agent consumed a certificate that gold kept
            add("customer_harm", "certificate_forfeited", max(0.0, face - applied_by_agent.get(key[1], 0.0)), f"{key[0]}:{key[1]}")
    for key in set(ac) - set(ic):
        if key in gc:
            delta = ac[key] - gc[key]
            if delta > 0:
                add("payout_loss", "excess_compensation", delta, f"{key[0]}:{key[1]}")
            elif delta < 0:
                add("omission", "short_compensation", delta, f"{key[0]}:{key[1]}")
        else:
            add("payout_loss", "unwarranted_compensation", ac[key], f"{key[0]}:{key[1]}")
    for key in set(gc) - set(ic) - set(ac):
        add("omission", "withheld_compensation", gc[key], f"{key[0]}:{key[1]}")
    return d


# --- tau2 integration -------------------------------------------------------------------------

def _db_dict(env) -> dict[str, Any]:
    return env.tools.db.model_dump(mode="json")


def _fresh(task, domain="airline", env_kwargs=None):
    from copy import deepcopy
    from tau2.registry import registry
    env = registry.get_env_constructor(domain)(**deepcopy(env_kwargs or {}))
    init = task.initial_state
    env.set_state(initialization_data=init.initialization_data if init else None,
                  initialization_actions=init.initialization_actions if init else None,
                  message_history=(init.message_history if init and init.message_history else []) or [],
                  strict=True)
    return env


def initial_db(task, domain="airline", env_kwargs=None) -> dict[str, Any]:
    return _db_dict(_fresh(task, domain, env_kwargs))


def gold_and_agent_dbs(task, messages, domain: str = "airline", env_kwargs: dict | None = None):
    """Rebuild the gold and agent end-state DBs exactly as tau2's EnvironmentEvaluator does.

    ``messages`` must be the full trajectory (including any task initial message history).
    """
    from copy import deepcopy
    from tau2.registry import registry

    ctor = registry.get_env_constructor(domain)
    init = task.initial_state
    agent_env = ctor(**deepcopy(env_kwargs or {}))
    agent_env.set_state(initialization_data=init.initialization_data if init else None,
                        initialization_actions=init.initialization_actions if init else None,
                        message_history=list(messages), strict=True)
    gold_env = _fresh(task, domain, env_kwargs)
    for action in (task.evaluation_criteria.actions or []):
        try:
            gold_env.make_tool_call(tool_name=action.name, requestor=action.requestor, **action.arguments)
        except Exception:  # mirror tau2: a failing gold action is skipped
            pass
    return _db_dict(gold_env), _db_dict(agent_env)
