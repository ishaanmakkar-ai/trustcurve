"""Framework for authoring tasks: builders + replay checker."""
import json, copy
TASKS=[]; META={}
_counter={'n':0}

def A(name, **args):
    return {"name": name, "arguments": args}

def add(stratum, purpose, policies, persona, reason, known, instr, actions=(), agent_data=None,
        unknown=None, notes=None, requester=None, outcome='', moves=False, opp='none',
        reason_cat='none', pressure='none', incident=None, boundary=None):
    _counter['n']+=1
    tid=f"X1-{_counter['n']:03d}"
    acts=[]
    for i,a in enumerate(actions):
        acts.append({"action_id": f"{tid}_{i}", "requestor": "assistant", "name": a['name'], "arguments": a['arguments'], "info": None})
    task={
      "id": tid,
      "description": {"purpose": purpose, "relevant_policies": policies, "notes": notes},
      "user_scenario": {"persona": persona, "instructions": {"domain": "airline", "reason_for_call": reason,
            "known_info": known, "unknown_info": unknown, "task_instructions": instr}},
      "initial_state": ({"initialization_data": {"agent_data": agent_data, "user_data": None}} if agent_data else None),
      "evaluation_criteria": {"actions": acts, "communicate_info": [], "nl_assertions": [], "reward_basis": ["DB"]},
    }
    TASKS.append(task)
    META[tid]={"stratum": stratum, "requester_user_id": requester, "correct_outcome": outcome,
               "gold_moves_money": moves, "money_opportunity": opp, "cancel_reason_category": reason_cat,
               "pressure": pressure, "incident_source": incident, "boundary": boundary}
    return tid
