"""Helpers for building author-b task records (scratch only)."""

TASKS = []
META = {}
_n = [0]


def fl(fn, d):
    return {"flight_number": fn, "date": d}


def pax(first, last, dob):
    return {"first_name": first, "last_name": last, "dob": dob}


def _act(name, args):
    _n[0] += 1
    return {"action_id": f"{name}_{_n[0]}", "requestor": "assistant", "name": name,
            "arguments": args, "info": None}


def cancel(rid):
    return _act("cancel_reservation", {"reservation_id": rid})


def cert(uid, amount):
    return _act("send_certificate", {"user_id": uid, "amount": amount})


def transfer(summary):
    return _act("transfer_to_human_agents", {"summary": summary})


def upd_flights(rid, cabin, flights, pid):
    return _act("update_reservation_flights", {"reservation_id": rid, "cabin": cabin,
                                                "flights": flights, "payment_id": pid})


def upd_bags(rid, total, nonfree, pid):
    return _act("update_reservation_baggages", {"reservation_id": rid, "total_baggages": total,
                                                 "nonfree_baggages": nonfree, "payment_id": pid})


def upd_pax(rid, passengers):
    return _act("update_reservation_passengers", {"reservation_id": rid, "passengers": passengers})


def book(uid, origin, dest, ftype, cabin, flights, passengers, payments, total_bags, nonfree, ins):
    return _act("book_reservation", {
        "user_id": uid, "origin": origin, "destination": dest, "flight_type": ftype,
        "cabin": cabin, "flights": flights, "passengers": passengers,
        "payment_methods": [{"payment_id": p, "amount": a} for p, a in payments],
        "total_baggages": total_bags, "nonfree_baggages": nonfree, "insurance": ins})


def task(num, *, stratum, user, purpose, policies, persona, reason, known, task_instructions,
         unknown=None, agent_data=None, actions=(), notes=None, correct_outcome, moves,
         opportunity, cancel_reason="none", pressure="none", incident=None, boundary=None):
    tid = f"X2b-{num:03d}"
    assert all(t["id"] != tid for t in TASKS), tid
    assert all(m["requester_user_id"] != user for m in META.values()), user
    TASKS.append({
        "id": tid,
        "description": {"purpose": purpose, "relevant_policies": policies, "notes": notes},
        "user_scenario": {
            "persona": persona,
            "instructions": {
                "domain": "airline",
                "reason_for_call": reason,
                "known_info": known,
                "unknown_info": unknown,
                "task_instructions": task_instructions,
            },
        },
        "initial_state": ({"initialization_data": {"agent_data": agent_data, "user_data": None}}
                          if agent_data else None),
        "evaluation_criteria": {"actions": list(actions), "communicate_info": [],
                                "nl_assertions": [], "reward_basis": ["DB"]},
    })
    META[tid] = {
        "stratum": stratum,
        "requester_user_id": user,
        "correct_outcome": correct_outcome,
        "gold_moves_money": moves,
        "money_opportunity": opportunity,
        "cancel_reason_category": cancel_reason,
        "pressure": pressure,
        "incident_source": incident,
        "boundary": boundary,
    }
