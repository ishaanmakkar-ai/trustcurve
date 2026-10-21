import json
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
F=DB['flights']; U=DB['users']; R=DB['reservations']

NOW='2024-05-15T15:00:00'
def fstat(fn,d):
    return F[fn]['dates'].get(d,{}).get('status')
def summ(rid, show=True):
    r=R[rid]; u=U[r['user_id']]
    segs=[f"{x['flight_number']} {x['origin']}-{x['destination']} {x['date']} ${x['price']} [{fstat(x['flight_number'],x['date'])}]" for x in r['flights']]
    s=(f"{rid} user={r['user_id']}({u['membership']}) {r['flight_type']} {r['cabin']} pax={len(r['passengers'])} ins={r['insurance']} created={r['created_at']} bags={r['total_baggages']}/{r['nonfree_baggages']} status={r.get('status')}\n   "
       + "\n   ".join(segs) + f"\n   pay={r['payment_history']}\n   pax={[p['first_name']+' '+p['last_name'] for p in r['passengers']]}")
    if show: print(s)
    return s
def usumm(uid):
    u=U[uid]
    print(uid, u['name'], u['membership'], 'dob',u['dob'])
    for k,v in u['payment_methods'].items(): print('   ',k,v.get('brand',''),v.get('last_four',''),v.get('amount',''))
    print('   saved:',u['saved_passengers']); print('   res:',u['reservations'])

def sts(r): return [fstat(x['flight_number'],x['date']) for x in r['flights']]
def find(pred, n=8, show=True):
    out=[]
    for rid,r in R.items():
        u=U[r['user_id']]
        try:
            ok=pred(r,u)
        except Exception as e:
            ok=False
        if ok:
            out.append(rid)
    if show:
        for rid in out[:n]: summ(rid)
        print('total',len(out))
    return out

def line(rid):
    r=R[rid]; u=U[r['user_id']]
    fl=" ".join(f"{x['flight_number']}:{x['origin']}-{x['destination']}@{x['date'][5:]}${x['price']}[{fstat(x['flight_number'],x['date'])[:3]}]" for x in r['flights'])
    pm=",".join(k.split('_')[0][:2]+k[-3:] for k in u['payment_methods'])
    return f"{rid} {r['user_id']}({u['membership'][:3]}) {r['flight_type'][:3]} {r['cabin'][:5]} p{len(r['passengers'])} ins={r['insurance']} cr={r['created_at'][5:16]} b{r['total_baggages']}/{r['nonfree_baggages']} pay={r['payment_history'][0]['payment_id'][:4]}{r['payment_history'][0]['amount']} | {fl} | pm={pm}"
def fl(pred, n=8):
    out=[rid for rid,r in R.items() if pred(r,U[r['user_id']])]
    for rid in out[:n]: print(line(rid))
    print('  total',len(out)); return out
def avail(r): return all(s=='available' for s in sts(r))
def old(r, d='2024-05-12'): return r['created_at']<d

def direct(o,d,date):
    out=[]
    for f in F.values():
        if f['origin']==o and f['destination']==d and date in f['dates']:
            v=f['dates'][date]
            out.append((f['flight_number'],f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],v['status'],v.get('prices'),v.get('available_seats')))
    return sorted(out,key=lambda x:x[1])
def pdirect(o,d,date):
    for x in direct(o,d,date): print('  ',date,o,d,x)

def pms(uid):
    u=U[uid]
    return ", ".join(f"{k}{'('+str(v.get('amount'))+')' if 'amount' in v else '('+v['brand']+' '+v['last_four']+')'}" for k,v in u['payment_methods'].items())
