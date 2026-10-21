import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
for rid in sys.argv[1:]:
    R=DB['reservations'][rid]; U=DB['users'][R['user_id']]
    print(rid,R['user_id'],U['membership'],R['cabin'],R['flight_type'],'pax',[p['first_name']+' '+p['last_name']+' '+p['dob'] for p in R['passengers']],'ins',R['insurance'],'bags',R['total_baggages'],R['nonfree_baggages'],R['created_at'])
    tot={}
    for f in R['flights']:
        x=DB['flights'][f['flight_number']]['dates'][f['date']]
        print('  ',f['flight_number'],f['date'],f['origin'],f['destination'],'paid',f['price'],x['status'],x.get('prices'),x.get('available_seats'))
        if 'prices' in x:
            for c,p in x['prices'].items(): tot[c]=tot.get(c,0)+p
    print('   current totals per pax',tot,'paid per pax',sum(f['price'] for f in R['flights']), 'payhist',R['payment_history'])
