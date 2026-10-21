"""Run any list of tau2 airline tasks (originals, variants, refusal tasks) with a chosen agent and
user simulator, keeping the communicate judge fixed (Haiku 5.5), and save tau2's results.json.

Usage (keys are read from ~/.config/trustcurve/env by scripts/with_keys.sh, never printed):
  python scripts/run_tasks.py --tasks-json path.json|--task-ids 0 1 2 \
      --agent-llm anthropic/claude-haiku-5-5 --user-llm openai/gpt-6.1-sol \
      --trials 2 --conc 8 --out results/raw/<name>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--tasks-json")
    g.add_argument("--task-ids", nargs="+")
    ap.add_argument("--agent-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--user-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--judge-llm", default="anthropic/claude-haiku-5-5")
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--conc", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261021)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from loguru import logger
    logger.remove()
    import tau2  # noqa: F401
    from tau2.data_model.semantic_communication import CommunicateScoring, SemanticCommunicateSettings
    from tau2.data_model.simulation import TextRunConfig
    from tau2.data_model.tasks import Task
    from tau2.runner.batch import run_tasks

    if a.tasks_json:
        tasks = [Task.model_validate(t) for t in json.loads(Path(a.tasks_json).read_text())]
    else:
        root = Path(tau2.__file__).resolve().parents[2] / "data" / "tau2" / "domains" / "airline" / "tasks.json"
        allt = {str(t["id"]): t for t in json.loads(root.read_text())}
        tasks = [Task.model_validate(allt[i]) for i in a.task_ids]

    cfg = TextRunConfig(
        domain="airline", agent="llm_agent", user="user_simulator",
        llm_agent=a.agent_llm, llm_args_agent={}, llm_user=a.user_llm, llm_args_user={},
        num_trials=a.trials, seed=a.seed, max_concurrency=a.conc, max_retries=3, retry_delay=1.0,
        auto_resume=True,  # rerunning into the same --out resumes from tau2's checkpoint (PILOT.md rate-limit plan)
        communicate_scoring=CommunicateScoring(judge=SemanticCommunicateSettings(model=a.judge_llm, model_args={})),
    )
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    res = run_tasks(cfg, tasks, save_path=out / "results.json", console_display=False)
    n = len(res.simulations)
    ok = sum(1 for s in res.simulations if s.reward_info and s.reward_info.reward == 1.0)
    print(json.dumps({"runs": n, "passed": ok, "out": str(out / "results.json")}))


if __name__ == "__main__":
    main()
