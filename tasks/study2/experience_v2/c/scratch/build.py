import json, sys, copy
sys.path.insert(0,'.')
import common
import t_cancel, t_change, t_book, t_comp, t_other
from lib import env
OUT='..'
tasks=[];meta={}
for task,m in common.TASKS:
    ad=(task['initial_state'] or {}).get('initialization_data',{}).get('agent_data') if task['initial_state'] else None
    e=env(ad)
    before=e.tools.db.model_dump()
    log=[]
    for a in task['evaluation_criteria']['actions']:
        fn=getattr(e.tools,a['name'])
        r=fn(**copy.deepcopy(a['arguments']))
    after=e.tools.db.model_dump()
    money=False; notes=[]
    for rid,R in after['reservations'].items():
        B=before['reservations'].get(rid)
        if B is None: money=True; notes.append('NEW %s pay=%s'%(rid,R['payment_history']))
        elif B['payment_history']!=R['payment_history']:
            money=True; notes.append('%s pay+=%s'%(rid,R['payment_history'][len(B['payment_history']):]))
        elif B!=R: notes.append('%s changed (no payment)'%rid)
    for uid,U in after['users'].items():
        if U['payment_methods']!=before['users'][uid]['payment_methods']:
            new=[k for k in U['payment_methods'] if k not in before['users'][uid]['payment_methods']]
            if any(k.startswith('certificate_3221') for k in new): money=True
            notes.append('%s pm: %s'%(uid,{k:U['payment_methods'][k].get('amount') for k in U['payment_methods'] if U['payment_methods'][k]!=before['users'][uid]['payment_methods'].get(k)}))
    m['gold_moves_money']=money
    tasks.append(task); meta[task['id']]=m
    print(task['id'],m['stratum'],m['requester_user_id'],'money' if money else '-', m['pressure'], '; '.join(notes))
assert len(tasks)==len(set(t['id'] for t in tasks))
json.dump(tasks,open(OUT+'/tasks.json','w'),indent=2)
json.dump(meta,open(OUT+'/meta.json','w'),indent=2)
from collections import Counter
print(len(tasks), Counter(m['stratum'] for m in meta.values()))
print('money', sum(m['gold_moves_money'] for m in meta.values()), 'pushback', sum(m['pressure']!='none' for m in meta.values()), 'incident', sum(bool(m['incident_source']) for m in meta.values()))
us=[m['requester_user_id'] for m in meta.values()]; print('dup users',[u for u,c in Counter(us).items() if c>1])
P=json.load(open('../../user_partitions.json'))['c']; print('not in partition',[u for u in us if u not in P])
