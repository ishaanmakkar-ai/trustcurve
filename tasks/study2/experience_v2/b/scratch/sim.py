import sys, json, os, copy
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.tools import AirlineTools
from tau2.domains.airline.utils import AIRLINE_DB_PATH
from tau2.utils.pydantic_utils import update_pydantic_model_with_dict
out = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tasks = json.load(open(os.path.join(out, "tasks.json")))
base = FlightDB.load(AIRLINE_DB_PATH)
for t in tasks:
    db = base.model_copy(deep=True)
    ini = (t.get("initial_state") or {}).get("initialization_data") or {}
    if ini.get("agent_data"):
        db = update_pydantic_model_with_dict(db, ini["agent_data"])
    tools = AirlineTools(db)
    msgs = []
    for a in t["evaluation_criteria"]["actions"]:
        f = getattr(tools, a["name"])
        try:
            r = f(**a["arguments"])
            if a["name"] in ("cancel_reservation", "update_reservation_flights", "update_reservation_baggages", "book_reservation"):
                msgs.append(f"{a['name']}:{r.reservation_id} pay={[ (p.payment_id,p.amount) for p in r.payment_history]}")
            else:
                msgs.append(f"{a['name']}:{str(r)[:80]}")
        except Exception as e:
            msgs.append(f"ERROR {a['name']}: {e}")
    print(t["id"], " | ".join(msgs) if msgs else "(no actions)")
