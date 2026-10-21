import json, lib
import t_cancel, t_change, t_book, t_comp, t_other
json.dump(lib.TASKS, open('../tasks.json','w'), indent=1)
json.dump(lib.META, open('../meta.json','w'), indent=1)
print(len(lib.TASKS))
