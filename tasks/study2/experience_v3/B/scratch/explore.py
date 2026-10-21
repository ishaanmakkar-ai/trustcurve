import json,collections
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('../../../experience_v3_main_partitions.json'))
print(DB.keys(), len(DB['users']), len(DB['reservations']), len(DB['flights']))
# flight status distribution by date
c=collections.Counter()
for f in DB['flights'].values():
    for d,s in f['dates'].items(): c[(d,s['status'])]+=1
for k in sorted(c): print(k,c[k])
