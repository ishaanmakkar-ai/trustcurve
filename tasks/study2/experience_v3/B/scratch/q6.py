from lib import *
def show(o,d,day):
    for x in direct(o,d,day): print(f"  {o}-{d} {day} {x[0]} dep{x[1]} {x[3]} seats{x[4]}")
show('ATL','MCO','2024-05-24')   # B02
show('BOS','MIA','2024-05-21')   # B03
show('DEN','LAS','2024-05-25'); show('LAS','DEN','2024-05-28') # B04/B05
show('JFK','MIA','2024-05-22')   # B08
show('ORD','DEN','2024-05-26')   # B09
show('SFO','SEA','2024-05-20'); show('SEA','SFO','2024-05-23') # B10
show('DTW','CLT','2024-05-19')   # B11
show('MIA','BOS','2024-05-25')   # B12
