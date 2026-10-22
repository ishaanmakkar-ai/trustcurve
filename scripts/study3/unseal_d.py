"""Phase D′ unseal (STUDY3.md §C′3, §C′6). Run ONLY after results/study3/phaseC/score_c.json is committed.

1. Refuses unless score_c.json and forecasts_frozen.json are tracked and unmodified in git.
2. Re-verifies every seal (SEAL.txt overall 5297f6be…, per source, pool hashes).
3. Reads each source's params.json generically (type / rate / non-monetary flags per configuration) and the sealed
   fault logs (counting only event == "draw"): realised opportunities and firings per configuration in F2's own runs
   (uw-F2-<cfg>) and in the experience period (exp-<cfg>-S/L).
4. Exposure-conditional H2: share flagged among H2-set configurations with >= 1 firing in F2's runs (natural
   configurations always count as exposed); deployment-relevant set: >= 1 firing in experience.
5. Writes the designer-known matching packet (Study 3 types + Study 2 §D descriptions) for a fresh-context agent.

Usage: python scripts/study3/unseal_d.py
"""

from __future__ import annotations

import glob
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
S = ROOT / "study3_sealed"


def committed(p: Path) -> bool:
    t = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", str(p)], capture_output=True).returncode == 0
    clean = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", str(p)]).returncode == 0
    return p.exists() and t and clean


def verify_seals():
    parts = {s: hashlib.sha256((S / s / "fault_impl.py").read_bytes() + (S / s / "params.json").read_bytes()).hexdigest()
             for s in ("designed", "external", "mechanical")}
    seal_txt = (ROOT / "results/study3/phaseB/SEAL.txt").read_text()
    for s, h in parts.items():
        assert h in seal_txt, f"seal mismatch for {s}"
    roster = re.search(r"roster\s+([0-9a-f]{64})", seal_txt).group(1)
    overall = hashlib.sha256((parts["designed"] + parts["external"] + parts["mechanical"] + roster).encode()).hexdigest()
    assert overall in seal_txt, "overall seal mismatch"
    return parts, overall


def firing_counts(pattern):
    c = defaultdict(lambda: {"opportunities": 0, "fired": 0})
    for f in glob.glob(str(S / "fault_logs" / pattern)):
        for line in open(f):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("event", "draw") == "draw":
                c[e.get("cfg_id")]["opportunities"] += 1; c[e.get("cfg_id")]["fired"] += bool(e.get("fired"))
    return c


def main():
    from trustcurve.study3.configs import CONFIGS3, H2_SET
    sc, fz = ROOT / "results/study3/phaseC/score_c.json", ROOT / "results/study3/forecasts_frozen.json"
    assert committed(sc) and committed(fz), "blind score / frozen forecasts not committed: refusing to unseal"
    parts, overall = verify_seals()
    params = {}
    for s in ("designed", "external", "mechanical"):
        P = json.loads((S / s / "params.json").read_text())
        params.update(P.get("configs", P))
    uw = firing_counts("uw-F2-*.jsonl"); ex = firing_counts("exp-*.jsonl")
    frozen = json.loads(fz.read_text()); det = frozen["detection"]["F2"]
    per = {}
    for c, v in CONFIGS3.items():
        if v.source == "clean":
            continue
        natural = v.source == "natural"
        per[c] = {"source": v.source, "params": params.get(c), "flag_primary": det[c]["flag_primary"],
                  "uw_F2": dict(uw[c]), "experience": dict(ex[c]),
                  "exposed_in_F2": natural or uw[c]["fired"] > 0, "fired_in_experience": natural or ex[c]["fired"] > 0}
    exp_set = [c for c in H2_SET if per[c]["exposed_in_F2"]]
    out = {"seal_verified": True, "overall": overall, "per_config": per,
           "H2_exposure_conditional": {"set": exp_set,
                                       "share": (sum(per[c]["flag_primary"] for c in exp_set) / len(exp_set)) if exp_set else None},
           "deployment_relevant": [c for c in per if per[c]["fired_in_experience"]]}
    (ROOT / "results/study3/phaseD").mkdir(parents=True, exist_ok=True)
    (ROOT / "results/study3/phaseD/unsealed.json").write_text(json.dumps(out, indent=1, default=str))
    s2d = (ROOT / "STUDY2.md").read_text()
    m = re.search(r"## D\..*?(?=\n## [A-Z]\.)", s2d, re.S)
    packet = {"study2_phaseD_text": m.group(0) if m else "", "study3_types": {c: per[c]["params"] for c in per}}
    (ROOT / "results/study3/phaseD/designer_known_packet.json").write_text(json.dumps(packet, indent=1, default=str))
    print(json.dumps({"overall": overall, "H2_exposure_conditional": out["H2_exposure_conditional"],
                      "deployment_relevant": len(out["deployment_relevant"])}))


if __name__ == "__main__":
    main()
