import json, sys
from loguru import logger
logger.remove()
from tau2.domains.airline.environment import get_environment
from tau2.data_model.tasks import Task

def run(task):
    env=get_environment()
    t=Task.model_validate(task)
    ad=(task.get('initial_state') or {}).get('initialization_data',{}) or {}
    ad=ad.get('agent_data')
    if ad: env.tools.update_db(ad)
    before=env.tools.db.model_dump()
    out=[]
    for a in task['evaluation_criteria']['actions']:
        fn=getattr(env.tools,a['name'])
        res=fn(**a['arguments'])
        out.append((a['name'], str(res)[:0]))
    after=env.tools.db.model_dump()
    # diffs
    lines=[]
    for rid,r in after['reservations'].items():
        b=before['reservations'].get(rid)
        if b!=r:
            if b is None:
                lines.append(f"NEW {rid} {r['cabin']} {[ (f['flight_number'],f['date'],f['price']) for f in r['flights']]} pay={r['payment_history']} bags={r['total_baggages']}/{r['nonfree_baggages']} ins={r['insurance']}")
            else:
                newpay=r['payment_history'][len(b['payment_history']):]
                ch=[k for k in r if r[k]!=b[k]]
                lines.append(f"MOD {rid} changed={ch} newpay={newpay} status={r.get('status')} cabin={r['cabin']} flights={[ (f['flight_number'],f['date'],f['price']) for f in r['flights']]} bags={r['total_baggages']}/{r['nonfree_baggages']}")
    for uid,u in after['users'].items():
        b=before['users'][uid]
        if b['payment_methods']!=u['payment_methods']:
            for k in set(u['payment_methods'])|set(b['payment_methods']):
                x=b['payment_methods'].get(k); y=u['payment_methods'].get(k)
                if x!=y: lines.append(f"PM {uid} {k}: {x and x.get('amount')} -> {y and y.get('amount')}")
    return lines

if __name__=='__main__':
    import importlib
    sys.path.insert(0,'.')
    tasks=json.load(open(sys.argv[1]))
    sel=set(sys.argv[2:])
    for t in tasks:
        if sel and t['id'] not in sel: continue
        try:
            ls=run(t)
            print(t['id'], 'OK', '| '.join(ls) if ls else '(no change)')
        except Exception as e:
            print(t['id'],'ERROR',repr(e))
