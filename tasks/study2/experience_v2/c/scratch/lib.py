import json, copy
from tau2.domains.airline.environment import get_environment
DBP='/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'
DB=json.load(open(DBP))
def env(agent_data=None):
    e=get_environment()
    if agent_data: e.tools.update_db(agent_data)
    return e
def direct(o,d,date,ad=None):
    e=env(ad)
    return [(f.flight_number,f.scheduled_departure_time_est,f.scheduled_arrival_time_est,dict(f.prices),dict(f.available_seats)) for f in e.tools.search_direct_flight(o,d,date)]
def onestop(o,d,date,ad=None):
    e=env(ad)
    out=[]
    for a,b in e.tools.search_onestop_flight(o,d,date):
        out.append(((a.flight_number,a.date,a.scheduled_departure_time_est,dict(a.prices)),(b.flight_number,b.date,b.scheduled_departure_time_est,dict(b.prices)), {k:a.prices[k]+b.prices[k] for k in a.prices}))
    return out
def fdate(fn,date):
    return DB['flights'][fn]['dates'].get(date)
