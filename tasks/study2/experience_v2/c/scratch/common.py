TASKS=[]
def A(name, **args):
    return (name, args)
def T(n, stratum, user, purpose, policies, persona, reason, known, task_instr, actions=(), unknown=None,
      agent_data=None, outcome='', money_opp='none', reason_cat='none', pressure='none', incident=None, boundary=None, notes=None):
    tid='X2c-%03d'%n
    acts=[]
    for i,(name,args) in enumerate(actions):
        acts.append({"action_id":"%s-%d"%(tid,i+1),"requestor":"assistant","name":name,"arguments":args,"info":None})
    task={"id":tid,
      "description":{"purpose":purpose,"relevant_policies":policies,"notes":notes},
      "user_scenario":{"persona":persona,"instructions":{"domain":"airline","reason_for_call":reason,"known_info":known,"unknown_info":unknown,"task_instructions":task_instr}},
      "initial_state":({"initialization_data":{"agent_data":agent_data,"user_data":None}} if agent_data else None),
      "evaluation_criteria":{"actions":acts,"communicate_info":[],"nl_assertions":[],"reward_basis":["DB"]}}
    writes={'book_reservation','cancel_reservation','update_reservation_flights','update_reservation_baggages','update_reservation_passengers','send_certificate'}
    money=False
    for name,args in actions:
        if name in ('book_reservation','cancel_reservation','send_certificate'): money=True
    meta={"stratum":stratum,"requester_user_id":user,"correct_outcome":outcome,"gold_moves_money":None,
          "money_opportunity":money_opp,"cancel_reason_category":reason_cat,"pressure":pressure,"incident_source":incident,"boundary":boundary}
    TASKS.append((task,meta))
