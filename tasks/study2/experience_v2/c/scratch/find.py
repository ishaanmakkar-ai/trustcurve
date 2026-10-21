import json
from lib import DB
P=json.load(open('../../user_partitions.json'))
allp=set(sum(P.values(),[]))
mine=set(P['c'])
print('users not in any partition:',[u for u in DB['users'] if u not in allp][:20], len(DB['users']), len(allp))
# reservations with cancelled or delayed flights, among my users
for u in P['c']:
    U=DB['users'][u]
    for r in U['reservations']:
        R=DB['reservations'][r]
        st=[DB['flights'][f['flight_number']]['dates'].get(f['date'],{}).get('status') for f in R['flights']]
        if any(s in ('cancelled','delayed','flying','on time') for s in st):
            print(u,U['membership'],r,R['cabin'],R['insurance'],len(R['passengers']),st)
