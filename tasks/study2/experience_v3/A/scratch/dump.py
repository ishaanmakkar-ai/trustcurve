import json,sys
from datetime import datetime
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('../../../experience_v3_main_partitions.json'))
NOW=datetime(2024,5,15,15,0,0)
def fstat(fn,d):
    x=DB['flights'][fn]['dates'].get(d)
    return x['status'] if x else 'NA'
for u in P['A']:
    U=DB['users'][u]
    pm=', '.join(f"{k}:{v['source'][0]}{('$'+str(v.get('amount'))) if 'amount' in v else ''}" for k,v in U['payment_methods'].items())
    print(f"== {u} [{U['membership']}] {U['name']['first_name']} {U['name']['last_name']} dob {U['dob']} | {pm} | saved:{[p['first_name']+' '+p['last_name'] for p in U['saved_passengers']]}")
    for r in U['reservations']:
        R=DB['reservations'][r]
        h=(NOW-datetime.fromisoformat(R['created_at'])).total_seconds()/3600
        fl=' '.join(f"{f['flight_number']}@{f['date']}({f['origin']}-{f['destination']},${f['price']},{fstat(f['flight_number'],f['date'])})" for f in R['flights'])
        pay=','.join(f"{p['payment_id']}:{p['amount']}" for p in R['payment_history'])
        print(f"   {r} {R['flight_type']} {R['cabin']} pax{len(R['passengers'])} ins={R['insurance']} bags{R['total_baggages']}/{R['nonfree_baggages']} {R.get('status') or ''} created {R['created_at']} ({h:.1f}h) | {fl} | pay {pay}")
