from lib import *
import itertools
# B01: eco in (150,250], BE<=150, on dates 05-20..05-24
c=[]
for f in F.values():
    for d in ['2024-05-20','2024-05-21','2024-05-22']:
        x=f['dates'][d]
        p=x['prices']; 
        if 150<p['economy']<=250 and p['basic_economy']<=120: c.append(('B01',f['flight_number'],f['origin'],f['destination'],d,f['scheduled_departure_time_est'],p))
print(c[:6])
# business one-way between 681-886 (with insurance 30)
c=[f"{f['flight_number']} {f['origin']}-{f['destination']} {d} {f['scheduled_departure_time_est']} {f['dates'][d]['prices']}" for f in F.values() for d in ['2024-05-24','2024-05-25'] if 650<=f['dates'][d]['prices']['business']<=880]
print('B04',c[:8])
