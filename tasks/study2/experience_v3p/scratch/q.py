import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
F=DB['flights']
def fl(num,date=None):
    f=F[num]; out=f"{num} {f['origin']}-{f['destination']} {f['scheduled_departure_time_est']}-{f['scheduled_arrival_time_est']}"
    ds=[date] if date else sorted(f['dates'])
    for d in ds:
        x=f['dates'].get(d); 
        if x is None: out+=f"\n  {d}: none"; continue
        out+=f"\n  {d}: {x['status']} " + (f"{x.get('prices')} seats{x.get('available_seats')}" if x['status']=='available' else str({k:v for k,v in x.items() if k!='status'}))
    return out
def direct(o,d,date):
    r=[]
    for f in F.values():
        if f['origin']==o and f['destination']==d and date in f['dates']:
            x=f['dates'][date]
            r.append(f"{f['flight_number']} {f['scheduled_departure_time_est']}-{f['scheduled_arrival_time_est']} {x['status']} {x.get('prices','')} {x.get('available_seats','')}")
    return r
def onestop(o,d,date):
    r=[]
    for f1 in F.values():
        if f1['origin']!=o or date not in f1['dates'] or f1['dates'][date]['status']!='available': continue
        d2 = f"2024-05-{int(date[-2:])+1}" if '+1' in f1['scheduled_arrival_time_est'] else date
        for f2 in F.values():
            if f2['origin']==f1['destination'] and f2['destination']==d and d2 in f2['dates'] and f2['dates'][d2]['status']=='available' and f2['scheduled_departure_time_est']>=f1['scheduled_arrival_time_est']:
                p1=f1['dates'][date]['prices'];p2=f2['dates'][d2]['prices']
                r.append(f"{f1['flight_number']}({f1['scheduled_departure_time_est']}-{f1['scheduled_arrival_time_est']})+{f2['flight_number']}@{d2}({f2['scheduled_departure_time_est']}-{f2['scheduled_arrival_time_est']}) be{p1['basic_economy']+p2['basic_economy']} e{p1['economy']+p2['economy']} b{p1['business']+p2['business']} seats {f1['dates'][date]['available_seats']} {f2['dates'][d2]['available_seats']}")
    return r
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='fl': print(fl(*sys.argv[2:]))
    elif cmd=='d': print("\n".join(direct(*sys.argv[2:])))
    elif cmd=='o': print("\n".join(onestop(*sys.argv[2:])))
    elif cmd=='res': print(json.dumps(DB['reservations'][sys.argv[2]],indent=1))
    elif cmd=='user': print(json.dumps(DB['users'][sys.argv[2]],indent=1))
