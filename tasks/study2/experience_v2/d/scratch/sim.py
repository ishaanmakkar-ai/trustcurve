import json,sys
from tau2.domains.airline.data_model import FlightDB
from tau2.domains.airline.tools import AirlineTools
from tau2.domains.airline.utils import AIRLINE_DB_PATH
from tau2.utils.pydantic_utils import update_pydantic_model_with_dict
def run(agent_data, actions, verbose=True):
    db=FlightDB.load(AIRLINE_DB_PATH)
    if agent_data: db=update_pydantic_model_with_dict(db,agent_data)
    t=AirlineTools(db)
    out=[]
    for name,args in actions:
        r=getattr(t,name)(**args)
        if hasattr(r,'model_dump'): r=r.model_dump()
        out.append(r)
        if verbose:
            if isinstance(r,dict) and 'payment_history' in r:
                print(name,'->',r['payment_history'],'cabin',r['cabin'],[ (f['flight_number'],f['date'],f['price']) for f in r['flights']], 'bags',r['total_baggages'],r['nonfree_baggages'])
            else: print(name,'->',r)
    return t,out
if __name__=='__main__':
    spec=json.loads(sys.argv[1])
    run(spec.get('init'),spec['actions'])
