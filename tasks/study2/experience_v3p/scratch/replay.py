# replay gold on fresh env; print money movements
import json, sys
from tau2.domains.airline.environment import get_environment
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.utils import AIRLINE_DB_PATH
from tau2.utils.pydantic_utils import update_pydantic_model_with_dict
tasks = json.load(open(sys.argv[1]))
only = sys.argv[2:]
for t in tasks:
    if only and t["id"] not in only: continue
    db = FlightDB.load(AIRLINE_DB_PATH)
    init = (t.get("initial_state") or {}).get("initialization_data") or {}
    if init.get("agent_data"): db = update_pydantic_model_with_dict(db, init["agent_data"])
    env = get_environment(db=db)
    tools = env.tools
    print("==", t["id"])
    for a in t["evaluation_criteria"]["actions"]:
        try:
            r = getattr(tools, a["name"])(**a["arguments"])
            if a["name"] in ("update_reservation_flights","update_reservation_baggages","cancel_reservation","book_reservation"):
                print("  ", a["name"], r.reservation_id, "payments:", [(p.payment_id,p.amount) for p in r.payment_history], "bags", r.total_baggages, r.nonfree_baggages, "cabin", r.cabin)
            else:
                print("  ", a["name"], str(r)[:120])
        except Exception as e:
            print("   ERROR", a["name"], e)
