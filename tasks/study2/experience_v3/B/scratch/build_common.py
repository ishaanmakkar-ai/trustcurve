"""Shared helpers for building the X3b task batch (scratch only)."""
import json
from lib import DB, F, U, R, price, hours_ago

TASKS = []
META = {}


def A(tid, n, name, args):
    return {"action_id": f"{tid}-a{n}", "requestor": "assistant", "name": name,
            "arguments": args, "info": None}


def flights(*pairs):
    return [{"flight_number": f, "date": d} for f, d in pairs]


def booking_total(fl, cabin, npax, insurance, nonfree):
    t = sum(price(f["flight_number"], f["date"], cabin) for f in fl) * npax
    if insurance == "yes":
        t += 30 * npax
    t += 50 * nonfree
    return t


def add(tid, *, stratum, requester, purpose, policies, persona, reason, known,
        instr, unknown=None, agent_data=None, actions=None, notes=None,
        correct_outcome, money_opportunity, cancel_reason, pressure,
        incident=None, boundary, boundary_type):
    actions = actions or []
    write_names = {"book_reservation", "cancel_reservation", "update_reservation_flights",
                   "update_reservation_baggages", "update_reservation_passengers",
                   "send_certificate"}
    money_names = {"book_reservation", "cancel_reservation", "send_certificate"}
    moves = False
    for a in actions:
        if a["name"] in money_names:
            moves = True
        if a["name"] in ("update_reservation_flights",):
            moves = True  # flagged per task below if zero-diff
        if a["name"] == "update_reservation_baggages":
            rid = a["arguments"]["reservation_id"]
            base = (agent_data or {}).get("reservations", {}).get(rid, {}).get(
                "nonfree_baggages", R[rid]["nonfree_baggages"])
            if a["arguments"]["nonfree_baggages"] > base:
                moves = True
    task = {
        "id": tid,
        "description": {"purpose": purpose, "relevant_policies": policies, "notes": notes},
        "user_scenario": {
            "persona": persona,
            "instructions": {
                "domain": "airline",
                "reason_for_call": reason,
                "known_info": known,
                "unknown_info": unknown,
                "task_instructions": instr,
            },
        },
        "initial_state": ({"initialization_data": {"agent_data": agent_data, "user_data": None}}
                          if agent_data else None),
        "evaluation_criteria": {"actions": actions, "communicate_info": [],
                                "nl_assertions": [], "reward_basis": ["DB"]},
    }
    TASKS.append(task)
    META[tid] = {
        "stratum": stratum,
        "requester_user_id": requester,
        "correct_outcome": correct_outcome,
        "gold_moves_money": moves,
        "money_opportunity": money_opportunity,
        "cancel_reason_category": cancel_reason,
        "pressure": pressure,
        "incident_source": incident,
        "boundary": boundary,
        "boundary_type": boundary_type,
    }
