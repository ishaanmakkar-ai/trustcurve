"""Builds tasks.json and meta.json for author a (experience_v2) and replays gold on a fresh DB."""
import json, sys, copy
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
sys.path.insert(0, "/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/src")

TASKS = []
META = {}
N = [0]


def fi(fn, d):
    return {"flight_number": fn, "date": d}


def px(f, l, dob):
    return {"first_name": f, "last_name": l, "dob": dob}


def pay(pid, amt):
    return {"payment_id": pid, "amount": amt}


def A(name, **args):
    return (name, args)


def task(stratum, user, *, purpose, policies, persona, reason, known, task_instr, gold=(),
         unknown=None, agent_data=None, correct, money_opp, cat="none", pressure="none",
         incident=None, boundary=None, notes=None):
    N[0] += 1
    tid = f"X2a-{N[0]:03d}"
    actions = []
    for i, (name, args) in enumerate(gold):
        actions.append({"action_id": f"{tid}-{i}", "requestor": "assistant", "name": name,
                        "arguments": args, "info": None})
    t = {
        "id": tid,
        "description": {"purpose": purpose, "relevant_policies": policies, "notes": notes},
        "user_scenario": {
            "persona": persona,
            "instructions": {
                "domain": "airline",
                "reason_for_call": reason,
                "known_info": known,
                "unknown_info": unknown,
                "task_instructions": task_instr,
            },
        },
        "initial_state": ({"initialization_data": {"agent_data": agent_data, "user_data": None}}
                          if agent_data else None),
        "evaluation_criteria": {"actions": actions, "communicate_info": [], "nl_assertions": [],
                                "reward_basis": ["DB"]},
    }
    TASKS.append(t)
    moves = any(a["name"] in ("cancel_reservation", "book_reservation", "send_certificate")
                for a in actions)
    META[tid] = {
        "stratum": stratum,
        "requester_user_id": user,
        "correct_outcome": correct,
        "gold_moves_money": None,  # filled by replay
        "money_opportunity": money_opp,
        "cancel_reason_category": cat,
        "pressure": pressure,
        "incident_source": incident,
        "boundary": boundary,
    }
    return tid


exec(open(Path(__file__).parent / "tasks_def.py").read())


# ---------------- replay ----------------
def replay():
    from tau2.domains.airline.data_model import FlightDB
    from tau2.domains.airline.tools import AirlineTools
    from tau2.domains.airline.utils import AIRLINE_DB_PATH
    from tau2.utils.pydantic_utils import update_pydantic_model_with_dict
    base = FlightDB.load(AIRLINE_DB_PATH)
    users = set()
    for t in TASKS:
        tid = t["id"]
        db = base.model_copy(deep=True)
        if t["initial_state"]:
            db = update_pydantic_model_with_dict(db, t["initial_state"]["initialization_data"]["agent_data"])
        before = db.model_dump()
        tools = AirlineTools(db)
        out = []
        for a in t["evaluation_criteria"]["actions"]:
            res = getattr(tools, a["name"])(**copy.deepcopy(a["arguments"]))
            if a["name"] in ("update_reservation_flights", "update_reservation_baggages", "cancel_reservation", "book_reservation"):
                out.append(f"{a['name']}: pay_hist={[(p.payment_id, p.amount) for p in res.payment_history]}")
            else:
                out.append(f"{a['name']}: {str(res)[:120]}")
        after = tools.db.model_dump()
        # money moved?
        moved = False
        for uid in after["users"]:
            if after["users"][uid]["payment_methods"] != before["users"][uid]["payment_methods"]:
                moved = True
        for rid in after["reservations"]:
            b = before["reservations"].get(rid)
            if b is None or b["payment_history"] != after["reservations"][rid]["payment_history"] or b.get("status") != after["reservations"][rid].get("status"):
                moved = True
        META[tid]["gold_moves_money"] = moved
        u = META[tid]["requester_user_id"]
        assert u not in users, (tid, u)
        users.add(u)
        print(tid, META[tid]["stratum"], u, "moves" if moved else "-", META[tid]["pressure"], "|", "; ".join(out))


if __name__ == "__main__":
    replay()
    P = set(json.load(open(OUT.parent / "user_partitions.json"))["a"])
    for tid, m in META.items():
        assert m["requester_user_id"] in P, tid
    from collections import Counter
    print(Counter(m["stratum"] for m in META.values()))
    print("moves", sum(m["gold_moves_money"] for m in META.values()), "of", len(META))
    print("pressure", Counter(m["pressure"] for m in META.values()))
    print("incidents", sum(1 for m in META.values() if m["incident_source"]))
    print("money_opp none", sum(1 for m in META.values() if m["money_opportunity"] == "none"))
    json.dump(TASKS, open(OUT / "tasks.json", "w"), indent=2)
    json.dump(META, open(OUT / "meta.json", "w"), indent=2)
