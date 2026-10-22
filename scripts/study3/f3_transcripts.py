"""Fix the 10 sample transcripts per underwriter card BEFORE any F1 run (STUDY3.md §C′1; review 12 #12): the same 10
F1 task IDs at trial 0 for every agent card, stratified over the F1 pool's strata, seed 20261024.

Usage: python scripts/study3/f3_transcripts.py  -> results/study3/f3_transcript_ids.txt
"""

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
meta = json.loads((ROOT / "tasks/study2/underwriting/meta.json").read_text())
pool = {str(t["id"]) for t in json.loads((ROOT / "tasks/study2/underwriting/pool.json").read_text())}
rng = random.Random(20261024)
by = defaultdict(list)
for tid in sorted(pool):
    by[meta.get(tid, {}).get("stratum", "other")].append(tid)
for v in by.values():
    rng.shuffle(v)
pick = []
while len(pick) < 10:                                           # round-robin over strata
    for s in sorted(by):
        if by[s] and len(pick) < 10:
            pick.append(by[s].pop())
out = ROOT / "results/study3/f3_transcript_ids.txt"
out.write_text("\n".join(pick) + "\n")
print(pick)
