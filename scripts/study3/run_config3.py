"""Run one Study 3 configuration over a task file with a chosen customer simulator (STUDY3.md §B′/C′).

As Study 2's run_config.py, but with the Study 3 roster (register3) and the sealed fault log. The fault log goes to
study3_sealed/fault_logs/<run>.jsonl so the analyst never reads firings before the blind analysis.

  python scripts/study3/run_config3.py --config C0 --tasks <pool.json> [--task-ids-file ids.txt] \
      --user-llm anthropic/claude-haiku-5-5 --trials 3 --conc 6 --out results/raw/study3/<run> [--date-hint]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--task-ids-file")
    ap.add_argument("--user-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--judge-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--conc", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261025)
    ap.add_argument("--out", required=True)
    ap.add_argument("--date-hint", action="store_true")
    a = ap.parse_args()

    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    os.environ["TC2_HARNESS_LOG"] = str(out / "harness.jsonl")
    flog = ROOT / "study3_sealed" / "fault_logs"; flog.mkdir(parents=True, exist_ok=True)
    os.environ["TC3_FAULT_LOG"] = str(flog / f"{out.name}.jsonl")

    from loguru import logger
    logger.remove()
    import tau2  # noqa: F401
    from tau2.data_model.semantic_communication import CommunicateScoring, SemanticCommunicateSettings
    from tau2.data_model.simulation import TextRunConfig
    from tau2.data_model.tasks import Task
    from tau2.runner.batch import run_tasks

    from trustcurve.study3.configs import CONFIGS3, register3

    cfg = CONFIGS3[a.config]
    agent_name = register3(a.config)
    raw = json.loads(Path(a.tasks).read_text())
    if a.task_ids_file:
        keep = [x.strip() for x in Path(a.task_ids_file).read_text().split() if x.strip()]
        by = {str(t["id"]): t for t in raw}
        raw = [by[i] for i in keep]
    if a.date_hint:
        for t in raw:
            ins = t["user_scenario"]["instructions"]
            if isinstance(ins, dict):
                ins["known_info"] = ((ins.get("known_info") or "").rstrip() + " Today's date is Wednesday, 15 May 2024.").strip()
    tasks = [Task.model_validate(t) for t in raw]
    run_cfg = TextRunConfig(
        domain="airline", agent=agent_name, user="user_simulator",
        llm_agent=cfg.model, llm_args_agent={}, llm_user=a.user_llm, llm_args_user={},
        num_trials=a.trials, seed=a.seed, max_concurrency=a.conc, max_retries=3, retry_delay=1.0,
        auto_resume=True,
        communicate_scoring=CommunicateScoring(judge=SemanticCommunicateSettings(model=a.judge_llm, model_args={})),
    )
    res = run_tasks(run_cfg, tasks, save_path=out / "results.json", console_display=False)
    print(json.dumps({"config": a.config, "runs": len(res.simulations), "out": str(out / "results.json")}))


if __name__ == "__main__":
    main()
