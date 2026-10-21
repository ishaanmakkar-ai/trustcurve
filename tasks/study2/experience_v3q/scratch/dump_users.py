import json,sys
from datetime import datetime
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('../../experience_v3_partitions.json'))
NOW=datetime(2024,5,15,15,0,0)
for uid in P['e']:
    u=DB['users'][uid]
    pm=", ".join(f"{k}({v['source'][:2]}{'' if v['source']=='credit_card' else ':'+str(v.get('amount'))})" for k,v in u['payment_methods'].items())
    print(f"== {uid} {u['membership']} | {u['name']['first_name']} {u['name']['last_name']} dob {u['dob']} | {pm}")
    for rid in u['reservations']:
        r=DB['reservations'][rid]
        h=(NOW-datetime.fromisoformat(r['created_at'])).total_seconds()/3600
        fl=" ".join(f"{f['flight_number']}@{f['date']}[{f['origin']}-{f['destination']}]${f['price']}:{DB['flights'][f['flight_number']]['dates'].get(f['date'],{}).get('status')}" for f in r['flights'])
        pay=",".join(f"{p['payment_id']}:{p['amount']}" for p in r['payment_history'])
        print(f"   {rid} {r['flight_type']} {r['cabin']} pax{len(r['passengers'])} ins={r['insurance']} bags={r['total_baggages']}/{r['nonfree_baggages']} created {r['created_at']} ({h:.1f}h) st={r.get('status')} | {fl} | pay {pay}")
