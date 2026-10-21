"""Hash the sealed experience pool (STUDY3.md §B′4) without printing any task content.

Per author: sha256(tasks.json || meta.json) and the task count. Appends to results/study3/phaseB/POOL_SEAL.txt.
Usage: python scripts/study3/seal_pool.py
"""

import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POOL = ROOT / "tasks" / "study3_sealed"
lines = []
for d in sorted(p for p in POOL.iterdir() if p.is_dir()):
    t, m = (d / "tasks.json").read_bytes(), (d / "meta.json").read_bytes()
    lines.append(f"{date.today()}  {d.name}  {hashlib.sha256(t + m).hexdigest()}  tasks={len(json.loads(t))}")
out = ROOT / "results" / "study3" / "phaseB" / "POOL_SEAL.txt"
hdr = "" if out.exists() else ("Study 3 experience pool (sealed from the F2 designer). sha256(tasks.json || meta.json) per author.\n"
                               "E1-E6 = experience pool (420); E7 = candidate F2 representative arm (held; Ishaan's decision 3).\n")
with open(out, "a") as f:
    f.write(hdr + "\n".join(lines) + "\n")
print("\n".join(lines))
