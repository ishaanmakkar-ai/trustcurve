"""Experience sample for C′ (STUDY3.md §C′5): 200 of the 380 non-pilot pool tasks, the same for every configuration,
stratified by stratum x author (seed 20261025); split into disjoint Sonnet / luna halves by alternating within strata;
the listed order is the nested stratified run order (round-robin over strata, so any prefix is balanced).
Also writes the deployment stratum weights W (the 380-task pool mix). Writes ids into tasks/study3_sealed/ (task content
stays sealed); prints counts and hashes.

Usage: python scripts/study3/experience_sample.py
"""

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "tasks" / "study3_sealed"
meta = json.loads((S / "meta.json").read_text())
pilot = set((S / "pilot_ids.txt").read_text().split())
ids = sorted(t for t in meta if t not in pilot and not t.startswith("E7"))
assert len(ids) == 380, len(ids)
STRATA = ("cancel", "change", "book", "compensation", "other")
W = {h: round(sum(meta[t]["stratum"] == h for t in ids) / len(ids), 4) for h in STRATA}
rng = random.Random(20261025)
cells = defaultdict(list)
for t in ids:
    cells[(meta[t]["stratum"], t.split("-")[0])].append(t)
for v in cells.values():
    rng.shuffle(v)
# proportional allocation of 200 over (stratum, author) cells by largest remainder
raw = {k: 200 * len(v) / len(ids) for k, v in cells.items()}
alloc = {k: int(x) for k, x in raw.items()}
for k in sorted(raw, key=lambda k: raw[k] - alloc[k], reverse=True)[:200 - sum(alloc.values())]:
    alloc[k] += 1
by_stratum = defaultdict(list)
for (h, a), v in sorted(cells.items()):
    by_stratum[h] += v[:alloc[(h, a)]]
for v in by_stratum.values():
    rng.shuffle(v)
order = []                                                       # nested stratified order: round-robin over strata
while any(by_stratum.values()):
    for h in STRATA:
        if by_stratum[h]:
            order.append(by_stratum[h].pop())
assert len(order) == 200 and len(set(order)) == 200
sonnet, luna, seen = [], [], defaultdict(int)
for t in order:                                                  # alternate within strata
    h = meta[t]["stratum"]
    (sonnet if seen[h] % 2 == 0 else luna).append(t); seen[h] += 1
(S / "exp_order.txt").write_text("\n".join(order) + "\n")
(S / "exp_S_ids.txt").write_text("\n".join(sonnet) + "\n")
(S / "exp_L_ids.txt").write_text("\n".join(luna) + "\n")
(ROOT / "results/study3/W_deploy.json").write_text(json.dumps(W, indent=1))
h = lambda p: hashlib.sha256((S / p).read_bytes()).hexdigest()
print(json.dumps({"W": W, "n": len(order), "S": len(sonnet), "L": len(luna), "order_sha256": h("exp_order.txt"),
                  "S_sha256": h("exp_S_ids.txt"), "L_sha256": h("exp_L_ids.txt")}))
