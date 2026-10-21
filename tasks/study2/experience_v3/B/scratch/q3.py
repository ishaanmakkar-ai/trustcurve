from lib import *
print(F['HAT060']['scheduled_departure_time_est'],F['HAT060']['scheduled_arrival_time_est'],F['HAT288']['scheduled_departure_time_est'])
for day in ['2024-05-23','2024-05-25','2024-05-26']:
    for a in direct_any('JFK',day):
        for b in direct_any(a[0][2],day):
            if b[0][2]=='LAS' and b[1]>=a[2]: print(day,a[0],a[1],a[2],a[3]['economy'],b[0],b[1],b[3]['economy'])
print('HAT076 0523 now', price('HAT076','2024-05-23','economy'))
