from lib import *
def show(o,d,dates):
    for day in dates:
        print('  direct',o,d,day,[(x[0],x[1],x[3]) for x in direct(o,d,day)])
print('H08 IDN02H'); r=R['IDN02H']; print([ (x['flight_number'],x['date'],x['price']) for x in r['flights']])
for day in ['2024-05-23','2024-05-25','2024-05-26']:
    for a,b,d2 in onestop('JFK','LAS',day): print('  ',day,a[0][0],a[1],a[3]['economy'],b[0][0],b[1],b[3]['economy'],d2)
print('H09'); show('DTW','MSP',['2024-05-26','2024-05-27','2024-05-28'])
print('H12'); show('PHX','SFO',['2024-05-16']); print(F['HAT009']['dates']['2024-05-15'], F['HAT009']['scheduled_departure_time_est'])
print('H16 SF5VA1', [ (x['flight_number'],x['date'],x['price']) for x in R['SF5VA1']['flights']]); show('DEN','PHL',['2024-05-27','2024-05-28','2024-05-29','2024-05-30'])
print('H18', cabin_change_cost('WYT8OO','basic_economy'))
print('H21', cabin_change_cost('JX6LB3','business'), [ (x['flight_number'],x['date'],x['price'], price(x['flight_number'],x['date'],'business')) for x in R['JX6LB3']['flights']])
print('H19', cabin_change_cost('RME85U','business'))
print('H13', cabin_change_cost('4CRC2E','economy'),cabin_change_cost('4CRC2E','business'))
print('H01', cabin_change_cost('3FRNFB','economy'))
