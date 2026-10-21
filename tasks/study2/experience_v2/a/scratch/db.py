import json
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve/tasks/study2/experience_v2/user_partitions.json'))['a']
U=DB['users'];R=DB['reservations'];F=DB['flights']
def pm(u):
    out=[]
    for k,v in U[u]['payment_methods'].items():
        if v['source']=='credit_card': out.append(f"{k}({v['brand']} {v['last_four']})")
        else: out.append(f"{k}(${v['amount']})")
    return out
def fstat(fn,d):
    x=F[fn]['dates'].get(d); return x['status'] if x else 'NA'
def res_line(r):
    x=R[r]
    fl=' '.join(f"{f['flight_number']}@{f['date']}[{f['origin']}-{f['destination']} ${f['price']} {fstat(f['flight_number'],f['date'])}]" for f in x['flights'])
    pay=','.join(f"{p['payment_id']}:{p['amount']}" for p in x['payment_history'])
    return f"  {r} {x['cabin']} {x['flight_type']} pax={len(x['passengers'])} created={x['created_at']} ins={x['insurance']} bags={x['total_baggages']}/{x['nonfree_baggages']} st={x.get('status')} | {fl} | pay {pay}"
def fl(fn,d):
    f=F[fn]; x=f['dates'].get(d)
    return f"{fn} {f['origin']}-{f['destination']} {f['scheduled_departure_time_est']}-{f['scheduled_arrival_time_est']} {d} {x}"
def direct(o,dst,d):
    out=[]
    for fn,f in F.items():
        if f['origin']==o and f['destination']==dst and d in f['dates'] and f['dates'][d]['status']=='available':
            x=f['dates'][d]; out.append((fn,f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],x['prices'],x['available_seats']))
    return out
def onestop(o,dst,d):
    out=[]
    for fn,f in F.items():
        if f['origin']==o and d in f['dates'] and f['dates'][d]['status']=='available':
            d2=d
            if '+1' in f['scheduled_arrival_time_est']:
                d2=f"2024-05-{int(d[-2:])+1}"
            for fn2,f2 in F.items():
                if f2['origin']==f['destination'] and f2['destination']==dst and d2 in f2['dates'] and f2['dates'][d2]['status']=='available' and f2['scheduled_departure_time_est']>=f['scheduled_arrival_time_est']:
                    out.append((fn,d,f['destination'],fn2,d2,f['dates'][d]['prices'],f2['dates'][d2]['prices']))
    return out
def show(u):
    x=U[u]; print(u,x['name'],x['membership'],x['dob'],' '.join(pm(u)))
    print('  saved:',x['saved_passengers'])
    for r in x['reservations']:
        if r in R: print(res_line(r)); print('    pax:',R[r]['passengers'])
