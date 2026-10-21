import json
TASKS=[]; META={}
def A(i,name,**args):
    return {"action_id":f"a{i}","requestor":"assistant","name":name,"arguments":args,"info":None}
def T(n, stratum, user, purpose, policies, persona, reason, known, instr, actions=(), unknown=None, init=None,
      outcome="", moves=False, opp="none", reason_cat="none", pressure="none", incident=None, boundary=None, notes=None):
    tid=f"X2d-{n:03d}"
    acts=[]
    for i,(name,args) in enumerate(actions):
        acts.append(A(i,name,**args))
    task={"id":tid,
      "description":{"purpose":purpose,"relevant_policies":policies,"notes":notes},
      "user_scenario":{"persona":persona,"instructions":{"domain":"airline","reason_for_call":reason,"known_info":known,"unknown_info":unknown,"task_instructions":instr}},
      "initial_state":({"initialization_data":{"agent_data":init,"user_data":None}} if init else None),
      "evaluation_criteria":{"actions":acts,"communicate_info":[],"nl_assertions":[],"reward_basis":["DB"]}}
    TASKS.append(task)
    META[tid]={"stratum":stratum,"requester_user_id":user,"correct_outcome":outcome,"gold_moves_money":moves,
       "money_opportunity":opp,"cancel_reason_category":reason_cat,"pressure":pressure,"incident_source":incident,"boundary":boundary}
def F(*pairs):
    return [{"flight_number":f,"date":d} for f,d in pairs]
def P(*triples):
    return [{"first_name":a,"last_name":b,"dob":c} for a,b,c in triples]
