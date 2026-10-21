# usage: p.py FLIGHT:DATE ...   prints status/prices
import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
for a in sys.argv[1:]:
    n,d=a.split(':'); f=DB['flights'][n]; x=f['dates'].get(d)
    print(n,d,f"{f['origin']}-{f['destination']} {f['scheduled_departure_time_est'][:5]}-{f['scheduled_arrival_time_est'][:8]}", x and x['status'], x and x.get('prices'), x and x.get('available_seats'))
