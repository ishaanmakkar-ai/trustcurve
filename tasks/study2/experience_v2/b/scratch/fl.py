import sys, json; sys.path.insert(0, sys.path[0])
from db import *
# usage: fl.py ORIG DEST DATE  -> direct + onestop available ; or fl.py HATxxx [date]
a=sys.argv[1:]
F=db['flights']
def show(fn,d):
    x=F[fn]['dates'].get(d)
    f=F[fn]
    print(f"  {fn} {f['origin']}-{f['destination']} {d} dep {f['scheduled_departure_time_est']} arr {f['scheduled_arrival_time_est']} :: {json.dumps(x)}")
if a[0].startswith('HAT'):
    f=F[a[0]]
    ds=[a[1]] if len(a)>1 else sorted(f['dates'])
    for d in ds: show(a[0],d)
else:
    o,de,d=a
    print('direct:')
    for fn,f in F.items():
        if f['origin']==o and f['destination']==de and d in f['dates']: show(fn,d)
    print('onestop:')
    for fn,f in F.items():
        if f['origin']==o and d in f['dates'] and f['dates'][d]['status']=='available':
            for fn2,g in F.items():
                if g['origin']==f['destination'] and g['destination']==de and d in g['dates'] and g['dates'][d]['status']=='available' and g['scheduled_departure_time_est']>=f['scheduled_arrival_time_est'] and '+1' not in f['scheduled_arrival_time_est']:
                    p1=f['dates'][d]['prices'];p2=g['dates'][d]['prices']
                    print(f"  {fn}({f['scheduled_departure_time_est']}-{f['scheduled_arrival_time_est']}) + {fn2}({g['scheduled_departure_time_est']}-{g['scheduled_arrival_time_est']}) via {f['destination']} be {p1['basic_economy']}+{p2['basic_economy']} e {p1['economy']}+{p2['economy']} b {p1['business']}+{p2['business']} seats {f['dates'][d]['available_seats']} {g['dates'][d]['available_seats']}")
