import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve/tasks/study2/experience_v3_partitions.json'))['p']
users=sys.argv[1:] or P
for u in users:
    U=DB['users'][u]
    pm=", ".join(f"{k}" + (f"(${v['amount']})" if 'amount' in v else f"({v.get('brand')} {v.get('last_four')})") for k,v in U['payment_methods'].items())
    print(f"== {u} [{U['membership']}] {U['name']['first_name']} {U['name']['last_name']} dob {U['dob']} | {pm}")
    for r in U['reservations']:
        R=DB['reservations'][r]
        fl=" ".join(f"{f['flight_number']}:{f['origin']}-{f['destination']}@{f['date']}${f['price']}" for f in R['flights'])
        pay=",".join(f"{p['payment_id']}:{p['amount']}" for p in R['payment_history'])
        print(f"   {r} {R['flight_type']} {R['cabin']} pax{len(R['passengers'])} ins={R['insurance']} bags={R['total_baggages']}/{R['nonfree_baggages']} created={R['created_at']} st={R.get('status')} | {fl} | {pay}")
