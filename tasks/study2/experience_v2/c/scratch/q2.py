import sys,json
from lib import DB
def F(fn,d):
    x=DB['flights'][fn]; s=x['dates'].get(d)
    print(fn,x['origin'],x['destination'],x['scheduled_departure_time_est'],x['scheduled_arrival_time_est'],d,s)
def R(r):
    x=DB['reservations'][r]; print(r,json.dumps({k:v for k,v in x.items()}))
for a in sys.argv[1:]:
    if ':' in a: F(*a.split(':'))
    else: R(a)
