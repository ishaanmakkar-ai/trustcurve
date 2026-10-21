import json, datetime as dt, copy
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
F=DB['flights']; U=DB['users']; R=DB['reservations']
NOW=dt.datetime(2024,5,15,15,0,0)
def hours_ago(s): return (NOW-dt.datetime.fromisoformat(s)).total_seconds()/3600
def inst(fn,d): return F[fn]['dates'][d]
def price(fn,d,cab): return inst(fn,d)['prices'][cab]
def seats(fn,d,cab): return inst(fn,d)['available_seats'][cab]
def direct(o,de,d):
    out=[]
    for f in F.values():
        if f['origin']==o and f['destination']==de and d in f['dates'] and f['dates'][d]['status']=='available':
            x=f['dates'][d]; out.append((f['flight_number'],f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],x['prices'],x['available_seats']))
    return out
def onestop(o,de,d):
    out=[]
    for a in direct_any(o,d):
        d2=d if '+1' not in a[2] else (dt.date.fromisoformat(d)+dt.timedelta(days=1)).isoformat()
        for b in direct_any(a[0][1],d2):
            if b[0][2]==de and b[1]>=a[2]:
                out.append((a,b,d2))
    return out
def direct_any(o,d):
    out=[]
    for f in F.values():
        if f['origin']==o and d in f['dates'] and f['dates'][d]['status']=='available':
            x=f['dates'][d]; out.append(((f['flight_number'],f['origin'],f['destination']),f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],x['prices'],x['available_seats']))
    return out
def cabin_change_cost(rid,newcab):
    r=R[rid]; n=len(r['passengers'])
    new=sum(price(x['flight_number'],x['date'],newcab) for x in r['flights'])*n
    old=sum(x['price'] for x in r['flights'])*n
    return new-old,new,old
