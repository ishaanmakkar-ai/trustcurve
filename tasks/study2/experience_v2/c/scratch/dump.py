import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('../../user_partitions.json'))['c']
fl=DB['flights']
def fstat(fn,d):
    x=fl[fn]['dates'].get(d,{})
    s=x.get('status')
    if s=='available': return 'avail'
    return s
for u in P:
    U=DB['users'][u]
    pm=[]
    for k,v in U['payment_methods'].items():
        pm.append(k+('' if v['source']=='credit_card' else '=%s'%v['amount']))
    print('##',u,U['membership'],U['name']['first_name'],U['name']['last_name'],'dob',U['dob'],'|',' '.join(pm))
    for r in U['reservations']:
        R=DB['reservations'][r]
        fs=' '.join('%s:%s>%s@%s$%d[%s]'%(f['flight_number'],f['origin'],f['destination'],f['date'][5:],f['price'],fstat(f['flight_number'],f['date'])) for f in R['flights'])
        pay=' '.join('%s:%d'%(p['payment_id'],p['amount']) for p in R['payment_history'])
        print('  ',r,R['flight_type'],R['cabin'],'pax%d'%len(R['passengers']),'ins',R['insurance'],'bags%d/%d'%(R['total_baggages'],R['nonfree_baggages']),'created',R['created_at'],R.get('status') or '','|',fs,'|',pay)
