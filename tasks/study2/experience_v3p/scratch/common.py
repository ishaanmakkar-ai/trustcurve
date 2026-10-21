import itertools
TASKS = []
META = {}
_counter = itertools.count(1)

def A(name, **args):
    return {"action_id": f"{name}_{next(_counter)}", "requestor": "assistant", "name": name, "arguments": args, "info": None}

def fl(*pairs):
    return [{"flight_number": n, "date": d} for n, d in pairs]

def pax(*triples):
    return [{"first_name": f, "last_name": l, "dob": d} for f, l, d in triples]

def T(tid, *, purpose, policies, persona, reason, known, unknown, instr, actions,
      agent_data=None, notes=None, stratum, requester, outcome, moves, opp, reason_cat,
      pressure, incident, boundary, features):
    TASKS.append({
        "id": tid,
        "description": {"purpose": purpose, "relevant_policies": policies, "notes": notes},
        "user_scenario": {"persona": persona, "instructions": {
            "domain": "airline", "reason_for_call": reason, "known_info": known,
            "unknown_info": unknown, "task_instructions": instr}},
        "initial_state": {"initialization_data": {"agent_data": agent_data, "user_data": None}} if agent_data else None,
        "evaluation_criteria": {"actions": actions, "communicate_info": [], "nl_assertions": [], "reward_basis": ["DB"]},
    })
    META[tid] = {"stratum": stratum, "requester_user_id": requester, "correct_outcome": outcome,
                 "gold_moves_money": moves, "money_opportunity": opp, "cancel_reason_category": reason_cat,
                 "pressure": pressure, "incident_source": incident, "boundary": boundary,
                 "difficulty_features": features}

def status(flight, date, st, dep=None, arr=None, kind="estimated"):
    d = {"status": st}
    if st in ("delayed", "on time"):
        d["estimated_departure_time_est"] = dep; d["estimated_arrival_time_est"] = arr
    if st == "landed":
        d["actual_departure_time_est"] = dep; d["actual_arrival_time_est"] = arr
    return {"flights": {flight: {"dates": {date: d}}}}
