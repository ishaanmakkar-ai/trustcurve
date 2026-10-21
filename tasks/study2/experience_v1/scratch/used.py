import json,sys
sys.path.insert(0,'.')
import fw, importlib
for m in ['t_cancel','t_change','t_book','t_comp','t_other']:
    try: importlib.import_module(m)
    except ModuleNotFoundError: pass
USED=set()
from db import R
for t in fw.TASKS:
    USED.add(fw.META[t['id']]['requester_user_id'])
