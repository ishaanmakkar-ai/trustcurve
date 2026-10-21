import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
for a in sys.argv[1:]:
    fn,d=a.split('@'); f=DB['flights'][fn]; x=f['dates'].get(d)
    print(fn,d,f['origin'],f['destination'],f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],x)
