"""Blind $0 firing and validity replay of the sealed fault modules (review 12 #7; STUDY3.md §B′2).

Replays real Study 2 experience conversations (B0, Sonnet and luna customers) message by message: every recorded
assistant message is passed through each planted configuration's ``apply`` with the conversation-so-far as state and
the live toolkit (the run's executed tool calls are re-applied so the DB evolves as it did); ``policy`` is called once
per conversation. Checks per configuration: fires at least once, no internal errors logged, every output is an
AssistantMessage, the module never mutates the DB directly.

The analyst sees only pass/fail per check per configuration. Counts (opportunities, firings, errors) are written to
study3_sealed/replay/replay_counts.json.

Usage: python scripts/study3/replay_faults.py [n_runs_per_batch] [tag batch_dir ...]   (batch dirs under results/raw/)
"""

from __future__ import annotations

import json
import os
import random
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main(n=40, batches=("study2/exp-B0-S", "study2/exp-B0-L"), tag="study2"):
    from loguru import logger
    from tau2.data_model.message import AssistantMessage, ToolMessage, UserMessage
    from tau2.data_model.tasks import Task

    from trustcurve.study2.ledger import _db, _fresh_env
    from trustcurve.study3.configs import CONFIGS3, load_fault_module
    logger.remove()
    by_role = {"assistant": AssistantMessage, "user": UserMessage, "tool": ToolMessage}
    cfgs = [c for c in CONFIGS3.values() if c.fault_source]
    mods = {s: load_fault_module(s) for s in {c.fault_source for c in cfgs}}
    rng = random.Random(20261022)
    runs = []
    for b in batches:
        R = json.loads((ROOT / "results/raw" / b / "results.json").read_text())
        tasks = {str(t["id"]): t for t in R["tasks"]}
        sims = [s for s in R["simulations"] if s.get("messages")]
        rng.shuffle(sims)
        runs += [(s, tasks[str(s["task_id"])]) for s in sims[:n]]
    stats = {c.id: {"opportunities": 0, "fired": 0, "errors": 0, "invalid": 0, "db_mutations": 0, "altered": 0,
                    "exceptions": 0} for c in cfgs}
    for s, traw in runs:
        task = Task.model_validate(traw)
        for c in cfgs:
            mod = mods[c.fault_source]
            log = tempfile.mktemp(suffix=".jsonl"); os.environ["TC3_FAULT_LOG"] = log
            env = _fresh_env(task); tk = env.tools
            if hasattr(mod, "policy"):
                try:
                    mod.policy(c.id, env.get_policy())
                except Exception:  # noqa: BLE001
                    stats[c.id]["exceptions"] += 1
            hist = []
            for m in s["messages"]:
                if m.get("role") not in by_role:
                    continue
                msg = by_role[m["role"]].model_validate(m)
                if m["role"] == "assistant":
                    before = _db(env)
                    try:
                        out = mod.apply(c.id, msg, SimpleNamespace(messages=list(hist)), tk, str(task.id))
                        if not isinstance(out, AssistantMessage):
                            stats[c.id]["invalid"] += 1
                        elif out != msg:
                            stats[c.id]["altered"] += 1
                    except Exception:  # noqa: BLE001
                        stats[c.id]["exceptions"] += 1
                    if _db(env) != before:
                        stats[c.id]["db_mutations"] += 1
                    for tc in (m.get("tool_calls") or []):       # evolve the DB as the real run did
                        try:
                            env.make_tool_call(tool_name=tc["name"], requestor="assistant", **(tc.get("arguments") or {}))
                        except Exception:  # noqa: BLE001
                            pass
                hist.append(msg)
            if os.path.exists(log):
                for line in open(log):
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ev = e.get("event", "draw")
                    if ev == "draw":
                        stats[c.id]["opportunities"] += 1; stats[c.id]["fired"] += bool(e.get("fired"))
                    elif ev == "error":
                        stats[c.id]["errors"] += 1
                os.remove(log)
    d = ROOT / "study3_sealed" / "replay"; d.mkdir(parents=True, exist_ok=True)
    (d / f"replay_counts_{tag}.json").write_text(json.dumps({"runs": len(runs), "stats": stats}, indent=1))
    flags = {cid: {"fires": v["fired"] > 0, "no_errors": v["errors"] == 0 and v["exceptions"] == 0,
                   "valid_outputs": v["invalid"] == 0, "no_db_mutation": v["db_mutations"] == 0} for cid, v in stats.items()}
    print(json.dumps({"runs_replayed": len(runs), "flags": flags}, indent=1))
    (ROOT / f"results/study3/phaseB/replay_flags_{tag}.json").write_text(json.dumps({"runs_replayed": len(runs), "flags": flags}, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) > 2:
        main(int(a[0]), tuple(a[2:]), a[1])
    else:
        main(int(a[0]) if a else 40)
