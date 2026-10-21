"""Merge the sealed experience pool (E1-E6) into one task file + meta, and draw the B′ fidelity-pilot sample
(STUDY3.md §B′4 / pilot amendment): 40 tasks, stratified by author (6-7 each) and stratum, fixed seed.
Writes only inside tasks/study3_sealed/ (gitignored); prints counts and hashes, no task content.

Usage: python scripts/study3/merge_pool.py
"""

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "tasks" / "study3_sealed"
SEED = 20261022
tasks, meta = [], {}
for a in ("E1", "E2", "E3", "E4", "E5", "E6"):
    tasks += json.loads((S / a / "tasks.json").read_text())
    meta |= json.loads((S / a / "meta.json").read_text())
assert len(tasks) == 420 and len({t["id"] for t in tasks}) == 420 and set(meta) >= {t["id"] for t in tasks}
(S / "pool.json").write_text(json.dumps(tasks)); (S / "meta.json").write_text(json.dumps(meta))
rng = random.Random(SEED)
by = defaultdict(list)
for t in tasks:
    by[t["id"].split("-")[0]].append(t["id"])
pilot = []
for i, (a, ids) in enumerate(sorted(by.items())):
    ids = sorted(ids, key=lambda x: (meta[x]["stratum"], x)); rng.shuffle(ids)
    k = 7 if i < 4 else 6                                   # 4 x 7 + 2 x 6 = 40
    strat = defaultdict(list)
    for x in ids:
        strat[meta[x]["stratum"]].append(x)
    pick = []
    while len(pick) < k:                                     # round-robin over strata
        for s in sorted(strat):
            if strat[s] and len(pick) < k:
                pick.append(strat[s].pop())
    pilot += pick
(S / "pilot_ids.txt").write_text("\n".join(pilot) + "\n")
h = lambda p: hashlib.sha256((S / p).read_bytes()).hexdigest()
print(json.dumps({"pool": len(tasks), "pilot": len(pilot), "pool_sha256": h("pool.json"), "meta_sha256": h("meta.json"),
                  "pilot_ids_sha256": h("pilot_ids.txt")}))
