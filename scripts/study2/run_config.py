"""Run one Study 2 configuration over a task file with a chosen customer simulator.

Usage (keys loaded by scripts/with_keys.sh, never printed):
  python scripts/study2/run_config.py --config B0 --tasks tasks/study2/underwriting/pool.json \
      --task-ids-file <optional ids.txt> --user-llm anthropic/claude-haiku-5-5 --trials 1 --conc 6 \
      --out results/raw/study2/<run-name>

The judge for COMMUNICATE checks is fixed at Haiku (as in Goal 3). Harness checks are logged to
<out>/harness.jsonl. Rerunning into the same --out resumes from tau2's checkpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--task-ids-file")
    ap.add_argument("--user-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--judge-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--conc", type=int, default=6)
    ap.add_argument("--seed", type=int, default=20261021)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    os.environ["TC2_HARNESS_LOG"] = str(out / "harness.jsonl")

    from loguru import logger
    logger.remove()
    import tau2  # noqa: F401
    from tau2.data_model.semantic_communication import CommunicateScoring, SemanticCommunicateSettings
    from tau2.data_model.simulation import TextRunConfig
    from tau2.data_model.tasks import Task
    from tau2.runner.batch import run_tasks

    from trustcurve.study2.configs import CONFIGS, register

    cfg = CONFIGS[a.config]
    agent_name = register(a.config)
    raw = json.loads(Path(a.tasks).read_text())
    if a.task_ids_file:
        keep = [x.strip() for x in Path(a.task_ids_file).read_text().split() if x.strip()]
        by = {str(t["id"]): t for t in raw}
        raw = [by[i] for i in keep]
    tasks = [Task.model_validate(t) for t in raw]
    run_cfg = TextRunConfig(
        domain="airline", agent=agent_name, user="user_simulator",
        llm_agent=cfg.model, llm_args_agent={}, llm_user=a.user_llm, llm_args_user={},
        num_trials=a.trials, seed=a.seed, max_concurrency=a.conc, max_retries=3, retry_delay=1.0,
        auto_resume=True,
        communicate_scoring=CommunicateScoring(judge=SemanticCommunicateSettings(model=a.judge_llm, model_args={})),
    )
    res = run_tasks(run_cfg, tasks, save_path=out / "results.json", console_display=False)
    n = len(res.simulations)
    ok = sum(1 for s in res.simulations if s.reward_info and s.reward_info.reward == 1.0)
    print(json.dumps({"config": a.config, "runs": n, "passed": ok, "out": str(out / "results.json")}))


if __name__ == "__main__":
    main()
