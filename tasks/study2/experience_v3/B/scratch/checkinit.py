import json
from loguru import logger; logger.remove()
from tau2.domains.airline.environment import get_environment
from tau2.data_model.tasks import Task
T=[Task.model_validate(t) for t in json.load(open('../tasks.json'))]
for t in T:
    if not t.initial_state: continue
    ad=t.initial_state.initialization_data.agent_data
    env=get_environment(); env.set_state(t.initial_state.initialization_data, None, [])
    db=env.tools.db
    for fn,v in ad.get('flights',{}).items():
        for d in v['dates']: print(t.id, fn, d, db.flights[fn].dates[d].model_dump())
    for rid,v in ad.get('reservations',{}).items():
        r=db.reservations[rid]; print(t.id, rid, {k:getattr(r,k) for k in v})
