import json, sys, importlib
sys.path.insert(0,'.')
import fw
for m in ['t_cancel','t_change','t_book','t_comp','t_other']:
    try: importlib.import_module(m)
    except ModuleNotFoundError as e:
        if e.name==m: print('skip',m); continue
        raise
out='/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve/tasks/study2/experience_v1/'
json.dump(fw.TASKS, open(out+'tasks.json','w'), indent=1)
json.dump(fw.META, open(out+'meta.json','w'), indent=1)
print(len(fw.TASKS),'tasks')
