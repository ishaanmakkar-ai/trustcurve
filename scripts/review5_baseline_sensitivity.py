"""Review 5 #5 (post-hoc, labelled): re-run the E1x analysis with the shared H x H baseline (pilot breadth, 01:49)
replaced by REF-H's contemporaneous runs on the same 25 tasks, and H x S replaced by REF-S. Both have 20 runs per task,
so per-task cell rates are means over 20 runs instead of 2. Written before the reference run finished.

Usage: PYTHONPATH=src python scripts/review5_baseline_sensitivity.py > results/phase1/review5_baseline_sensitivity.json
"""
import json

from trustcurve.phase1 import e1x, load

P = "results/phase1/"
B = set(open("results/pilot/breadth_tasks.txt").read().split())
refh = [r for r in load(P + "ref_H_runs.csv") if r["task_id"] in B]
refs = load(P + "ref_S_runs.csv")
cells = {("H", "H"): refh, ("H", "O"): load(P + "e1_O_runs.csv"), ("H", "S"): refs,
         ("S", "H"): load(P + "p1b_breadth_runs.csv"), ("S", "O"): load(P + "e1x_SO_runs.csv"), ("S", "S"): load(P + "e1x_SS_runs.csv")}
res = e1x(cells)
res["note"] = "post-hoc sensitivity (review 5 #5): HxH := REF-H on breadth tasks, HxS := REF-S; not pre-registered"
print(json.dumps(res, indent=1))
