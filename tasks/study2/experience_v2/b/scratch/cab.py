import sys, json; sys.path.insert(0, sys.path[0])
from db import *
F=db['flights']
for r in sys.argv[1:]:
    R=db['reservations'][r]; U=db['users'][R['user_id']]
    n=len(R['passengers']); old=sum(f['price'] for f in R['flights'])*n
    print(r, R['user_id'], U['membership'], R['cabin'], R['flight_type'], 'pax',n, 'bags',R['total_baggages'],R['nonfree_baggages'],'ins',R['insurance'],'paid',R['payment_history'], 'fare_total',old)
    print('   pax:', R['passengers'])
    for f in R['flights']:
        x=F[f['flight_number']]['dates'][f['date']]
        print('   ', f['flight_number'], f['origin'], f['destination'], f['date'], f['price'], x.get('status'), x.get('prices'), x.get('available_seats'))
    for c in ['basic_economy','economy','business']:
        try:
            new=sum(F[f['flight_number']]['dates'][f['date']]['prices'][c] for f in R['flights'])*n
            print('   to',c,'new',new,'diff',new-old)
        except Exception as e: print('   to',c,'NA')
