"""Overall flaw-catalogue seal (STUDY3.md §B′2): sha256 over designed || external || mechanical || roster, each part being
sha256(fault_impl.py || params.json) (roster = src/trustcurve/study3/configs.py). Prints hashes only.

Usage: python scripts/study3/seal_all.py
"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "study3_sealed"
parts = {}
for src in ("designed", "external", "mechanical"):
    parts[src] = hashlib.sha256((S / src / "fault_impl.py").read_bytes() + (S / src / "params.json").read_bytes()).hexdigest()
parts["roster"] = hashlib.sha256((ROOT / "src" / "trustcurve" / "study3" / "configs.py").read_bytes()).hexdigest()
overall = hashlib.sha256("".join(parts[k] for k in ("designed", "external", "mechanical", "roster")).encode()).hexdigest()
for k, v in parts.items():
    print(k, v)
print("overall", overall)
