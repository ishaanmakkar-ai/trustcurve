import json,sys
DB=json.load(open('/Users/ishaanmakkar/.local/share/trustcurve/tau2-bench/data/tau2/domains/airline/db.json'))
for r in sys.argv[1:]:
    x=DB['reservations'][r]; print(r, x['user_id'], x['origin'],'->',x['destination'],x['flight_type'],x['cabin'],'ins',x['insurance'],'bags',x['total_baggages'],x['nonfree_baggages'],x['created_at'])
    print('   pax',[(p['first_name'],p['last_name'],p['dob']) for p in x['passengers']])
    print('   pay',x['payment_history'])
