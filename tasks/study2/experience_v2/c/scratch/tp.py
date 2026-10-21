import json
from lib import DB
P=json.load(open('../../user_partitions.json'))
allp=set(sum(P.values(),[]))
for u in [u for u in DB['users'] if u not in allp]:
    U=DB['users'][u]
    for r in U['reservations']:
        R=DB['reservations'][r]
        if R['cabin']!='business' and R['insurance']=='no' and R['created_at']<'2024-05-13' and all(DB['flights'][f['flight_number']]['dates'].get(f['date'],{}).get('status')=='available' for f in R['flights']):
            print(u,U['membership'],U['dob'],r,R['cabin'],len(R['passengers']),R['flights'][0]['origin'],R['destination'],R['flights'][0]['date'],R['payment_history'])
