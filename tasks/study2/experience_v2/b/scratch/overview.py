import sys; sys.path.insert(0, sys.path[0])
from db import *
for u in P:
    U=db['users'][u]
    pms=', '.join(f"{k}{'('+str(v.get('amount'))+')' if 'amount' in v else ''}" for k,v in U['payment_methods'].items())
    print(f"== {u} [{U['membership']}] dob {U['dob']} | {pms}")
    for r in U['reservations']:
        R=db['reservations'][r]
        fl=' '.join(f"{f['flight_number']}:{f['origin']}-{f['destination']}@{f['date']}${f['price']}[{db['flights'][f['flight_number']]['dates'].get(f['date'],{}).get('status')}]" for f in R['flights'])
        pay=' '.join(f"{p['payment_id']}:{p['amount']}" for p in R['payment_history'])
        print(f"   {r} {R['flight_type']} {R['cabin']} pax{len(R['passengers'])} bags{R['total_baggages']}/{R['nonfree_baggages']} ins={R['insurance']} created {R['created_at']} st={R.get('status')} | {fl} | {pay}")
