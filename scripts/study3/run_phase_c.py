"""C′ orchestrator (STUDY3.md §C′1, §C′5): runs batches strictly one at a time through run_batch3.sh (spend guard
pre-check at a projected cost, fail-closed recording). Resumable: a batch whose runs CSV exists is skipped. Stops at
the first non-zero exit (gate, cap, unpriced runs, collection failure) and prints why.

  python scripts/study3/run_phase_c.py underwriting     # F1 (90 x 3) and F2 (frozen, x 3), 20 configs, Haiku customer
  python scripts/study3/run_phase_c.py experience       # 100 Sonnet (date hint) + 100 luna (date+stop hint) per config
  python scripts/study3/run_phase_c.py <mode> --dry     # print the plan and projected cost only
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from trustcurve.study3.configs import CONFIGS3  # noqa: E402

HAIKU, SONNET, LUNA = "anthropic/claude-haiku-5-5", "anthropic/claude-sonnet-5-5", "openai/gpt-6-luna"
# measured $/run (Study 2 spend.csv, Study 3 pilot); key = agent model short name (+ "pc" for the checker harness)
UW = {"claude-haiku-5-5": 0.012, "pc": 0.018, "claude-sonnet-5-5": 0.10, "claude-haiku-4-5-20251001": 0.113,
      "gpt-6-luna": 0.003, "gpt-4o-mini-2024-07-18": 0.015}
EXP = {"S": {"claude-haiku-5-5": 0.025, "pc": 0.027, "claude-sonnet-5-5": 0.135, "claude-haiku-4-5-20251001": 0.072,
             "gpt-6-luna": 0.016, "gpt-4o-mini-2024-07-18": 0.03},
       "L": {"claude-haiku-5-5": 0.006, "pc": 0.007, "claude-sonnet-5-5": 0.108, "claude-haiku-4-5-20251001": 0.044,
             "gpt-6-luna": 0.0013, "gpt-4o-mini-2024-07-18": 0.01}}
MARGIN = 1.5
F1 = (ROOT / "tasks/study2/underwriting/pool.json", ROOT / "tasks/study2/underwriting/meta.json", 90)
F2 = (ROOT / "tasks/study3/F2/pool.json", ROOT / "tasks/study3/F2/meta.json", None)
SEAL = ROOT / "tasks/study3_sealed"


def key(cfg):
    return "pc" if cfg.harness == "policy_check" else cfg.model.split("/")[-1]


def plan(mode):
    out = []
    if mode == "underwriting":
        n2 = len(__import__("json").loads(F2[0].read_text())) if F2[0].exists() else 0
        for bench, (pool, meta, n) in (("F1", F1), ("F2", F2)):
            n = n or n2
            for cid, cfg in CONFIGS3.items():
                out.append({"name": f"uw-{bench}-{cid}", "cfg": cid, "pool": pool, "meta": meta, "sim": HAIKU, "siml": "H",
                            "trials": 3, "ids": None, "env": {}, "proj": n * 3 * UW[key(cfg)] * MARGIN})
    else:
        for cid, cfg in CONFIGS3.items():
            for sim, siml, ids, env in ((SONNET, "S", SEAL / "exp_S_ids.txt", {"DATE_HINT": "1"}),
                                        (LUNA, "L", SEAL / "exp_L_ids.txt", {"DATE_HINT": "1", "STOP_HINT": "1"})):
                out.append({"name": f"exp-{cid}-{siml}", "cfg": cid, "pool": SEAL / "pool.json", "meta": SEAL / "meta.json",
                            "sim": sim, "siml": siml, "trials": 1, "ids": ids, "env": env,
                            "proj": 100 * EXP[siml][key(cfg)] * MARGIN})
    return out


def main(mode, dry=False):
    if mode == "underwriting" and not (F2[0].exists() and F2[1].exists()):
        print("F2 is not frozen (tasks/study3/F2/pool.json missing): STUDY3 §C′0 forbids any F1/F2 run before the freeze")
        return 2
    if mode == "experience" and not dry:
        fz = ROOT / "results/study3/forecasts_frozen.json"
        tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", str(fz)],
                                 capture_output=True).returncode == 0
        dirty = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", str(fz)]).returncode != 0
        if not fz.exists() or not tracked or dirty:
            print("Forecasts are not frozen and committed (results/study3/forecasts_frozen.json): no experience run (§C′4)")
            return 2
    P = plan(mode)
    print(f"{len(P)} batches; projected (with x{MARGIN} margin) ${sum(b['proj'] for b in P):.2f}")
    if dry:
        return 0
    for b in P:
        if (ROOT / "results/study3/runs" / f"{b['name']}.csv").exists():
            continue
        env = dict(os.environ, CONC="6", TRIALS=str(b["trials"]), **b["env"])
        args = [str(ROOT / "scripts/study3/run_batch3.sh"), "C", b["name"], b["cfg"], str(b["pool"]), str(b["meta"]),
                b["sim"], b["siml"], f"{b['proj']:.2f}"] + ([str(b["ids"])] if b["ids"] else [])
        rc = subprocess.call(args, env=env)
        print(b["name"], "exit", rc, flush=True)
        if rc != 0:
            print("STOPPED at", b["name"], "- see results/study3/logs/" + b["name"] + ".log")
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--dry" in sys.argv))
