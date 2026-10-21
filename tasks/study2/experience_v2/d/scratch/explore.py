import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('../../user_partitions.json'))['d']
U=DB['users'];R=DB['reservations'];F=DB['flights']
def fstat(fn,date):
    return F[fn]['dates'].get(date,{}).get('status')
for u in P:
    usr=U[u]
    pm=",".join(f"{k}:{v.get('amount','')}" for k,v in usr['payment_methods'].items())
    print(f"== {u} {usr['membership']} dob={usr['dob']} pm=[{pm}] saved={[p['first_name']+' '+p['last_name'] for p in usr['saved_passengers']]}")
    for rid in usr['reservations']:
        r=R[rid]
        fl=" ".join(f"{f['flight_number']}@{f['date']}({f['origin']}-{f['destination']},${f['price']},{fstat(f['flight_number'],f['date'])})" for f in r['flights'])
        pay=",".join(f"{p['payment_id']}:{p['amount']}" for p in r['payment_history'])
        print(f"   {rid} {r['flight_type']} {r['cabin']} pax={len(r['passengers'])} created={r['created_at']} bags={r['total_baggages']}/{r['nonfree_baggages']} ins={r['insurance']} st={r.get('status')} pay=[{pay}] :: {fl}")
