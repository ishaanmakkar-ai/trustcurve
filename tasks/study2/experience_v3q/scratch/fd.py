import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
cab=sys.argv[1]
for fn in sys.argv[2:]:
  f=DB['flights'][fn]; print(fn,f['origin'],f['destination'],f['scheduled_departure_time_est'],[(d[5:],x['prices'][cab],x['available_seats'][cab]) for d,x in f['dates'].items() if x['status']=='available'])
