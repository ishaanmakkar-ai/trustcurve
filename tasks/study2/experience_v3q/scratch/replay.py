"""Replay gold actions and print money deltas per task (independent check)."""
import json, copy
from datetime import datetime
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.tools import AirlineTools
from tau2.domains.airline.utils import AIRLINE_DB_PATH
from tau2.utils.pydantic_utils import update_pydantic_model_with_dict
NOW = datetime(2024,5,15,15,0,0)
tasks = json.load(open('../tasks.json')); meta = json.load(open('../meta.json'))
base = FlightDB.load(AIRLINE_DB_PATH)
for t in tasks:
    db = base.model_copy(deep=True)
    init = (t.get('initial_state') or {}).get('initialization_data') or {}
    if init.get('agent_data'): db = update_pydantic_model_with_dict(db, init['agent_data'])
    tools = AirlineTools(db)
    m = meta[t['id']]; u = m['requester_user_id']
    before = {k: v.model_dump() for k, v in tools.db.users[u].payment_methods.items()}
    outs = []
    for a in t['evaluation_criteria']['actions']:
        r = getattr(tools, a['name'])(**a['arguments'])
        if a['name'] in ('update_reservation_flights','update_reservation_baggages','cancel_reservation','book_reservation'):
            outs.append(f"{a['name']} {r.reservation_id} pay={[ (p.payment_id,p.amount) for p in r.payment_history]} bags={r.total_baggages}/{r.nonfree_baggages}")
        else: outs.append(f"{a['name']} -> {str(r)[:80]}")
    # sanity: every reservation mentioned in user's list belongs to them
    for rid in tools.db.users[u].reservations:
        assert tools.db.reservations[rid].user_id == u
    print(t['id'], u, m['stratum'], m['pressure'], 'bt', m['boundary_type'])
    for o in outs: print('    ', o)
