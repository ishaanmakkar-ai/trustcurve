import json, sys
from loguru import logger; logger.remove()
from tau2.domains.airline.environment import get_environment
from tau2.data_model.tasks import Task
T=[Task.model_validate(t) for t in json.load(open('../tasks.json'))]
for t in T:
    env=get_environment()
    idata=t.initial_state.initialization_data if t.initial_state else None
    if idata: env.set_state(idata, None, [])
    db=env.tools.db
    out=[]
    for a in t.evaluation_criteria.actions:
        before={k:(v.model_dump().get('amount')) for k,v in db.users[db.reservations[a.arguments['reservation_id']].user_id].payment_methods.items()} if 'reservation_id' in a.arguments else None
        res=getattr(env.tools,a.name)(**a.arguments)
        if a.name in ('update_reservation_flights','update_reservation_baggages'):
            r=db.reservations[a.arguments['reservation_id']]
            out.append(f"{a.name}:{r.payment_history[-1].payment_id}={r.payment_history[-1].amount}" if len(r.payment_history)>0 else a.name)
        elif a.name=='cancel_reservation':
            r=db.reservations[a.arguments['reservation_id']]; out.append(f"cancel refund {[ (p.payment_id,p.amount) for p in r.payment_history if p.amount<0]}")
        elif a.name=='book_reservation':
            out.append(f"book {res.reservation_id} {[(p.payment_id,p.amount) for p in res.payment_history]}")
        else: out.append(f"{a.name}:{str(res)[:60]}")
    # check flight statuses for injected flights
    print(t.id, out)
