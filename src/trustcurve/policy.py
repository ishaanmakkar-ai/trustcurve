"""Policy-compliance layer: is a divergence from gold actually a wrongful act?

A refund the agent issued that gold did not is only an insured *wrongful payout* if the airline
policy did not permit it. tau2's airline policy (policy.md, "Cancel flight") allows cancellation
when ANY of these holds:
  1. the booking was made within the last 24 hours,
  2. the flight was cancelled by the airline,
  3. it is a business-class reservation,
  4. the user has travel insurance and the reason is covered by insurance.
Rule 4 depends on the stated reason, which the DB does not record, so insured reservations
without rules 1-3 are returned as "uncertain" rather than guessed.

Found in pilot loop 3: an agent cancelled a business-class reservation at the customer's explicit
request (policy-permitted); gold kept it, so the raw diff showed a $4,418 "over-refund".
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping

# The airline policy states the current time.
NOW = datetime(2024, 5, 15, 15, 0, 0)


def cancellation_permission(res: Mapping[str, Any], flights_db: Mapping[str, Any] | None = None) -> str:
    """Return 'permitted', 'not_permitted' or 'uncertain' for cancelling this reservation."""
    created = datetime.fromisoformat(res["created_at"])
    if NOW - created <= timedelta(hours=24):
        return "permitted"
    if res.get("cabin") == "business":
        return "permitted"
    if flights_db:
        for f in res.get("flights", []):
            st = ((flights_db.get(f["flight_number"]) or {}).get("dates") or {}).get(f["date"]) or {}
            if st.get("status") == "cancelled":
                return "permitted"
    if res.get("insurance") == "yes":
        return "uncertain"
    return "not_permitted"


def classify_items(items: list[dict], agent_db: Mapping[str, Any]) -> list[dict]:
    """Annotate over-refund items with policy permission; other kinds pass through unchanged."""
    out = []
    for it in items:
        it = dict(it)
        if it["kind"] == "over_refund":
            rid = it["ref"].split(":")[0]
            res = agent_db.get("reservations", {}).get(rid)
            it["policy"] = cancellation_permission(res, agent_db.get("flights")) if res else "uncertain"
        out.append(it)
    return out


def insured_amounts(items: list[dict]) -> dict[str, float]:
    """Split payout/harm into clear wrongful vs policy-permitted vs uncertain."""
    tot = {"wrongful_payout": 0.0, "permitted_divergence": 0.0, "uncertain_payout": 0.0, "customer_harm": 0.0}
    for it in items:
        if it["category"] == "customer_harm":
            tot["customer_harm"] += it["usd"]
        elif it["category"] == "payout_loss":
            p = it.get("policy")
            if p == "permitted":
                tot["permitted_divergence"] += it["usd"]
            elif p == "uncertain":
                tot["uncertain_payout"] += it["usd"]
            else:
                tot["wrongful_payout"] += it["usd"]
    return tot
