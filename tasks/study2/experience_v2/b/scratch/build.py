import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
import t_cancel, t_change, t_book, t_comp, t_other
out = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tasks = sorted(lib.TASKS, key=lambda t: t["id"])
json.dump(tasks, open(os.path.join(out, "tasks.json"), "w"), indent=2)
json.dump({k: lib.META[k] for k in sorted(lib.META)}, open(os.path.join(out, "meta.json"), "w"), indent=2)
print(len(tasks), "tasks written")
