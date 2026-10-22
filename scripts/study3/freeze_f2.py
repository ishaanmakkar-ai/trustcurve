"""F2 freeze (STUDY3.md §C′0): merge the designer's trap tasks (<= 70) with the 40 sealed E7 tasks into
tasks/study3/F2/pool.json + meta.json, validate (gold replay, $0), and print the SHA-256 to commit before any F1/F2 run.

Usage: python scripts/study3/freeze_f2.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
F2 = ROOT / "tasks/study3/F2"
E7 = ROOT / "tasks/study3_sealed/E7"


def main():
    trap, tmeta = json.loads((F2 / "trap_pool.json").read_text()), json.loads((F2 / "trap_meta.json").read_text())
    assert 1 <= len(trap) <= 70, f"trap tasks must be 1..70, got {len(trap)}"
    assert all(str(t["id"]).startswith("F2-") for t in trap) and set(tmeta) >= {str(t["id"]) for t in trap}
    e7, e7meta = json.loads((E7 / "tasks.json").read_text()), json.loads((E7 / "meta.json").read_text())
    pool, meta = trap + e7, {**tmeta, **e7meta}
    (F2 / "pool.json").write_text(json.dumps(pool, indent=1)); (F2 / "meta.json").write_text(json.dumps(meta, indent=1))
    v = subprocess.run([sys.executable, str(ROOT / "scripts/study2/validate_tasks.py"), str(F2 / "pool.json"), str(F2 / "meta.json")],
                       capture_output=True, text=True)
    print(v.stdout[-600:])
    if v.returncode != 0:                                            # validate_tasks.py exits 1 if any task is invalid
        print("VALIDATION FAILED: fix trap tasks before freezing (after the freeze, invalid tasks are dropped, never edited)")
        return 1
    h = hashlib.sha256((F2 / "pool.json").read_bytes() + (F2 / "meta.json").read_bytes()).hexdigest()
    print(json.dumps({"trap": len(trap), "e7": len(e7), "total": len(pool), "sha256": h}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
