import json,sys,copy
DBP='/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'
DB=json.load(open(DBP))
U=DB['users'];R=DB['reservations'];F=DB['flights']
def res(rid):
    r=R[rid]; print(json.dumps(r,indent=None))
    for f in r['flights']:
        print('  ',f['flight_number'],f['date'],F[f['flight_number']]['dates'][f['date']].get('status'), F[f['flight_number']]['scheduled_departure_time_est'],F[f['flight_number']]['scheduled_arrival_time_est'])
def user(uid):
    u=U[uid]; print(json.dumps({k:u[k] for k in ['name','dob','membership','payment_methods','saved_passengers','reservations']}))
def direct(o,d,date):
    for fn,f in F.items():
        if f['origin']==o and f['destination']==d and date in f['dates']:
            s=f['dates'][date]
            print(fn,date,o,d,f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],s['status'],s.get('prices'),s.get('available_seats'))
def onestop(o,d,date):
    for fn,f in F.items():
        if f['origin']==o and date in f['dates'] and f['dates'][date]['status']=='available':
            for fn2,f2 in F.items():
                if f2['origin']==f['destination'] and f2['destination']==d and date in f2['dates'] and f2['dates'][date]['status']=='available' and f2['scheduled_departure_time_est']>=f['scheduled_arrival_time_est'] and '+1' not in f['scheduled_arrival_time_est']:
                    print(fn,fn2,f['destination'],f['scheduled_departure_time_est'],f2['scheduled_arrival_time_est'],f['dates'][date]['prices'],f2['dates'][date]['prices'])
def fl(fn,date=None):
    f=F[fn]; print(fn,f['origin'],f['destination'],f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'])
    for d,s in f['dates'].items():
        if date is None or d==date: print('  ',d,s)
if __name__=='__main__':
    cmd=sys.argv[1]; args=sys.argv[2:]
    globals()[cmd](*args)
