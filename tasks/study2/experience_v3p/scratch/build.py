import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import common, t_cancel, t_change, t_rest
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tasks = sorted(common.TASKS, key=lambda t: t["id"])
json.dump(tasks, open(os.path.join(OUT, "tasks.json"), "w"), indent=2)
meta = {k: common.META[k] for k in sorted(common.META)}
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=2)
print(len(tasks), "tasks written")
