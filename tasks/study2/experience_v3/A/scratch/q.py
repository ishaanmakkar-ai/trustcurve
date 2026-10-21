import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
def direct(o,d,date):
    out=[]
    for fn,f in DB['flights'].items():
        if f['origin']==o and f['destination']==d and date in f['dates']:
            x=f['dates'][date]
            out.append((fn,f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],x['status'],x.get('prices'),x.get('available_seats')))
    return sorted(out,key=lambda t:t[1])
def flight(fn,date=None):
    f=DB['flights'][fn]
    if date: return f['origin'],f['destination'],f['scheduled_departure_time_est'],f['dates'].get(date)
    return f
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='d':
        for r in direct(*sys.argv[2:5]): print(r)
    elif cmd=='f':
        print(flight(sys.argv[2],sys.argv[3]))
