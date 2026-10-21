import sys
from q import direct
for spec in sys.argv[1:]:
    o,d,date=spec.split(',')
    print('##',o,d,date)
    for r in direct(o,d,date): print('  ',r)
