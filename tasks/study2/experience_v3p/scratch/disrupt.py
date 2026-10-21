import json
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
P=json.load(open('/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve/tasks/study2/experience_v3_partitions.json'))['p']
for u in P:
    U=DB['users'][u]
    for r in U['reservations']:
        R=DB['reservations'][r]
        st=[]
        for f in R['flights']:
            x=DB['flights'][f['flight_number']]['dates'].get(f['date'],{}).get('status')
            st.append(f"{f['flight_number']}@{f['date'][5:]}:{x}")
        if any(s.split(':')[1] in ('cancelled','delayed','flying','on time') for s in st):
            print(u,U['membership'],r,R['cabin'],'ins',R['insurance'],'pax',len(R['passengers']),st)
