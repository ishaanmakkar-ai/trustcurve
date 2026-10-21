from lib import *
for rid in ['M9WKQM','34XLFT','Z8IPHP','429815','R37DI8','YX8BX4','B41JHU','C94NNS','JN75RZ','GYJ4P7','3JA7XV','1MYSZJ','K6O2E6','OXIY9U','AXYDVC','2N4HQI','AQHB3C','9J3E5I','Q0K59Y','UDDZ3N','V638TK','5U9JWB','58AXWI','BZKLPO','XPZTWZ','P0Q4SM','Z33MRB','8700JW']:
    r=R[rid]; print(rid, r['origin'],r['destination'], [ (p['first_name'],p['last_name'],p['dob']) for p in r['passengers']])
for u in ['juan_sanchez_3680','ivan_muller_7015','yara_silva_8071','fatima_sanchez_8117','harper_davis_5069','noah_gonzalez_5087','aarav_nguyen_9116','ava_sanchez_2625','omar_khan_7452','amelia_khan_5280']:
    x=U[u]; print(u, x['name'], x['dob'], x['saved_passengers'], {k:(v['source'],v.get('brand'),v.get('last_four'),v.get('amount')) for k,v in x['payment_methods'].items()})
