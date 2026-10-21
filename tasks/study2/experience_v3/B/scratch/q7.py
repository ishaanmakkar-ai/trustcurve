from lib import *
for fn,d in [('HAT045','2024-05-15'),('HAT276','2024-05-15'),('HAT131','2024-05-14'),('HAT204','2024-05-13'),('HAT204','2024-05-02'),('HAT009','2024-05-15'),('HAT102','2024-05-17'),('HAT265','2024-05-06'),('HAT150','2024-05-14'),('HAT298','2024-05-12'),('HAT020','2024-05-15'),('HAT162','2024-05-14'),('HAT296','2024-05-13')]:
    print(fn,d,F[fn]['scheduled_departure_time_est'],F[fn]['scheduled_arrival_time_est'],F[fn]['dates'][d])
for rid in ['WYT8OO','TI7NSI','IDN02H','3FRNFB','JX6LB3','4CRC2E','SF5VA1','867TY6']:
    r=R[rid]; print(rid,[(x['flight_number'],x['date'],inst(x['flight_number'],x['date']).get('available_seats')) for x in r['flights']])
for u in ['emma_kim_4489','raj_moore_8640','isabella_anderson_8228','james_ahmed_4322','mohamed_gonzalez_6188','evelyn_anderson_4579','lucas_brown_4047','amelia_sanchez_4739','yusuf_muller_4960','aarav_garcia_1177','sofia_rossi_7655','ivan_johansson_2235','harper_davis_5069']:
    print(u,{k:(v.get('brand'),v.get('last_four'),v.get('amount')) for k,v in U[u]['payment_methods'].items()})
print(R['P9L9FV']); print(R['QGR999']['origin'],R['QGR999']['destination'])
