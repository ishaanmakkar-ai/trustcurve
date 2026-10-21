import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
o,d,date=sys.argv[1:4]; cab=sys.argv[4] if len(sys.argv)>4 else 'economy'
out=[]
for fn,f in DB['flights'].items():
    if f['origin']==o and f['destination']==d and date in f['dates'] and f['dates'][date]['status']=='available':
        x=f['dates'][date]; out.append((x['prices'][cab],f"DIRECT {fn} {f['scheduled_departure_time_est']}-{f['scheduled_arrival_time_est']} {x['prices']} seats{x['available_seats']}"))
for fn,f in DB['flights'].items():
    if f['origin']==o and date in f['dates'] and f['dates'][date]['status']=='available' and f['destination']!=d:
        for fn2,f2 in DB['flights'].items():
            if f2['origin']==f['destination'] and f2['destination']==d:
                if '+1' in f['scheduled_arrival_time_est']: continue
                if f['scheduled_arrival_time_est']>f2['scheduled_departure_time_est']: continue
                x=f['dates'][date]; x2=f2['dates'].get(date)
                if x2 and x2['status']=='available':
                    out.append((x['prices'][cab]+x2['prices'][cab],f"1STOP {fn} {f['scheduled_departure_time_est']}-{f['scheduled_arrival_time_est']} {x['prices']} s{x['available_seats']} | {fn2} {f2['scheduled_departure_time_est']}-{f2['scheduled_arrival_time_est']} {x2['prices']} s{x2['available_seats']}"))
for p,s in sorted(out): print(p,s)
