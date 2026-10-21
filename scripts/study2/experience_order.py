"""Nested stratified order of the phase-C experience pool (review 7 #7).

Every prefix of the order tracks the deployment mix W (largest-deficit rule; random within stratum, seed fixed), so a
configuration with n_e tasks uses the first n_e and every pair of configurations shares min(n_e) tasks.
Usage: python scripts/study2/experience_order.py <meta.json> <out order.txt>
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from trustcurve.study2.forecast import STRATA, W_DEPLOY  # noqa: E402

meta = json.load(open(sys.argv[1])); rng = random.Random(20261024)
by = {h: sorted(k for k, m in meta.items() if m["stratum"] == h) for h in STRATA}
for h in by:
    rng.shuffle(by[h])
order, count = [], {h: 0 for h in STRATA}
while any(by[h] for h in STRATA):
    k = len(order) + 1
    h = max((h for h in STRATA if by[h]), key=lambda h: (W_DEPLOY[h] * k - count[h], -STRATA.index(h)))
    order.append(by[h].pop()); count[h] += 1
Path(sys.argv[2]).write_text("\n".join(order) + "\n")
for n in (30, 50, 100, 150, len(order)):
    pre = order[:n]
    print(n, {h: sum(meta[i]["stratum"] == h for i in pre) for h in STRATA})
