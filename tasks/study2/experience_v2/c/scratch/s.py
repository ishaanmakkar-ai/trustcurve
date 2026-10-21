import sys
from lib import DB
def direct(o,d,date):
    out=[]
    for fn,f in DB['flights'].items():
        if f['origin']==o and f['destination']==d and f['dates'].get(date,{}).get('status')=='available':
            x=f['dates'][date]; out.append((fn,f['scheduled_departure_time_est'],f['scheduled_arrival_time_est'],x['prices'],x['available_seats']))
    return out
for a in sys.argv[1:]:
    o,d,date=a.split(',')
    print('==',o,d,date)
    for r in direct(o,d,date): print('  ',r)
