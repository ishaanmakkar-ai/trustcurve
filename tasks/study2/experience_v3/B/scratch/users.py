import json
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('../../../experience_v3_main_partitions.json'))
F=DB['flights']
def fst(fl):
    s=F[fl['flight_number']]['dates'].get(fl['date'],{}).get('status','?')
    return s
for u in P['B']:
    U=DB['users'][u]
    pm=[(k, v.get('amount','')) for k,v in U['payment_methods'].items()]
    print(f"== {u} {U['membership']} pm={pm} saved={[p['first_name']+' '+p['last_name'] for p in U['saved_passengers']]}")
    for r in U['reservations']:
        R=DB['reservations'][r]
        fl=' '.join(f"{x['flight_number']}@{x['date'][5:]}:{x['origin']}-{x['destination']}${x['price']}[{fst(x)}]" for x in R['flights'])
        pay=[(p['payment_id'],p['amount']) for p in R['payment_history']]
        print(f"   {r} {R['cabin']} {R['flight_type']} pax={len(R['passengers'])} ins={R['insurance']} bags={R['total_baggages']}/{R['nonfree_baggages']} created={R['created_at']} st={R.get('status')} | {fl} | pay={pay}")
