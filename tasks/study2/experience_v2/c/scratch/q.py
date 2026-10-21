import sys; from lib import *
cmd=sys.argv[1]
if cmd=='d':
    for r in direct(*sys.argv[2:5]): print(r)
elif cmd=='o':
    for r in onestop(*sys.argv[2:5]): print(r)
elif cmd=='f':
    fn=sys.argv[2]; F=DB['flights'][fn]; print(F['origin'],F['destination'],F['scheduled_departure_time_est'],F['scheduled_arrival_time_est'])
    for d in sys.argv[3:]: print(d,F['dates'].get(d))
