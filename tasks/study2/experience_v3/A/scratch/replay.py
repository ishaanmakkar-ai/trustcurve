import json, sys
from pathlib import Path
from tau2.domains.airline.environment import get_environment
from tau2.data_model.tasks import Task
OUT = Path(__file__).resolve().parent.parent
tasks = [Task.model_validate(t) for t in json.load(open(OUT/'tasks.json'))]
for t in tasks:
    env = get_environment()
    if t.initial_state and t.initial_state.initialization_data:
        env.tools.update_db(t.initial_state.initialization_data.agent_data)
    db = env.tools.db
    out=[]
    for a in t.evaluation_criteria.actions:
        before = None
        res = getattr(env.tools, a.name)(**a.arguments)
        if a.name in ('update_reservation_flights','update_reservation_baggages','cancel_reservation'):
            r = res
            out.append(f"{a.name}: payhist={[ (p.payment_id,p.amount) for p in r.payment_history]}")
        elif a.name=='book_reservation':
            out.append(f"book: {res.reservation_id} pay={[ (p.payment_id,p.amount) for p in res.payment_history]} bags {res.total_baggages}/{res.nonfree_baggages}")
        else:
            out.append(f"{a.name}: {res}")
    print(t.id, '|', ' || '.join(out) if out else '(no writes)')
