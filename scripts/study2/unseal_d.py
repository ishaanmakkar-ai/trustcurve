"""Phase D unseal and scoring (STUDY2.md §D). Run ONLY after the blind report is committed.

1. Verifies sha256(fault_impl.py || params.json) equals results/study2/phaseD/SEAL.txt.
2. Reads params.json (planter's schema, parsed generically: a fault type and a rate per configuration; clean controls
   have no type or a type like none/clean/control) and fault_log.jsonl (realised firings).
3. Mutation score = share of planted fault TYPES (excluding controls) flagged by the primary eval (and with secondary
   signals included); false positives = controls flagged; blind recovery = blind excess event rate vs realised firing
   rate per task.

Usage: python scripts/study2/unseal_d.py <blind_report.json> <out unsealed.json>
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEALED = ROOT / "study2_sealed"
CLEAN = {"none", "clean", "control", "no_fault", "null", ""}


def _find(d: dict, pats):
    for k, v in d.items():
        if any(re.search(p, k, re.I) for p in pats):
            return v
    return None


def main(blind_path, out_path):
    impl, params = (SEALED / "fault_impl.py").read_bytes(), (SEALED / "params.json").read_bytes()
    sha = hashlib.sha256(impl + params).hexdigest()
    sealed = re.search(r"[0-9a-f]{64}", (ROOT / "results/study2/phaseD/SEAL.txt").read_text()).group(0)
    assert sha == sealed, f"seal mismatch: {sha} != {sealed}"
    P = json.loads(params)
    P = P.get("configs", P) if isinstance(P, dict) else P
    blind = json.load(open(blind_path))
    fires = defaultdict(lambda: {"opportunities": 0, "fired": 0, "tasks": set()})
    log = SEALED / "fault_log.jsonl"
    if log.exists():
        for line in log.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("event", "draw") != "draw":  # review 9 #1: the log also writes an "applied" line per firing
                continue
            c = r.get("cfg_id"); fires[c]["opportunities"] += 1; fires[c]["fired"] += bool(r.get("fired"))
            if r.get("fired"):
                fires[c]["tasks"].add(r.get("task_id"))
    per, types = {}, defaultdict(list)
    for c, spec in (P.items() if isinstance(P, dict) else ((s.get("id"), s) for s in P)):
        spec = spec if isinstance(spec, dict) else {"type": spec}
        ftype = str(_find(spec, [r"type", r"fault"]) or "none")
        rate = _find(spec, [r"rate", r"prob", r"^p$"])
        clean = ftype.strip().lower() in CLEAN
        b = blind.get(c, {})
        n_tasks = (b.get("commission_sign_test") or {}).get("n_tasks") or 90
        realised_rate = len(fires[c]["tasks"]) / n_tasks if n_tasks else None
        per[c] = {"fault_type": ftype, "planted_rate": rate, "clean_control": clean,
                  "realised_firings": fires[c]["fired"], "opportunities": fires[c]["opportunities"],
                  "realised_tasks_with_firing_rate": realised_rate,
                  "flag_primary": b.get("flag_primary"), "flag_any": b.get("flag_any"),
                  "blind_excess_event_rate_per_task": b.get("blind_excess_event_rate_per_task"),
                  "spec": spec}
        if not clean:
            types[ftype].append(c)
    det_p = {t: any(per[c]["flag_primary"] for c in cs) for t, cs in types.items()}
    det_a = {t: any(per[c]["flag_any"] for c in cs) for t, cs in types.items()}
    res = {"seal_verified": True, "sha256": sha, "per_config": per,
           "mutation_score_primary": (sum(det_p.values()) / len(det_p)) if det_p else None,
           "mutation_score_with_secondary": (sum(det_a.values()) / len(det_a)) if det_a else None,
           "types": {t: {"configs": cs, "detected_primary": det_p[t], "detected_any": det_a[t]} for t, cs in types.items()},
           "false_positives_primary": [c for c, v in per.items() if v["clean_control"] and v["flag_primary"]],
           "K4_fires": (sum(det_p.values()) / len(det_p) < 0.5) if det_p else None}
    Path(out_path).write_text(json.dumps(res, indent=1, default=list))
    print(json.dumps({k: res[k] for k in ("mutation_score_primary", "mutation_score_with_secondary",
                                           "false_positives_primary", "K4_fires")}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
