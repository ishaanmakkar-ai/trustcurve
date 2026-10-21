"""Run the statement judge on the 30-transcript validation sample (results/study3/audit_packs/statement/) and keep the
output SEALED (study3_sealed/judge_validation/<model>.json) until Ishaan's labels are in, so his labels cannot be
anchored on the judge. Prints counts and cost only. Run via scripts/with_keys.sh.

Usage: python scripts/study3/judge_validation.py claude-haiku-5-5
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
RAW = ROOT / "results" / "raw" / "study2"
META = ROOT / "tasks" / "study2" / "experience_main" / "meta.json"


def main(model):
    import anthropic
    from loguru import logger
    from tau2.data_model.tasks import Task
    from tau2.registry import registry

    from trustcurve.study3.judge import judge_run
    logger.remove()
    key = json.loads((ROOT / "study3_sealed" / "audit_keys" / "statement_key.json").read_text())
    meta = json.loads(META.read_text())
    policy = registry.get_env_constructor("airline")().get_policy()
    client = anthropic.Anthropic()
    cache, out, tot = {}, {}, 0.0
    for aid, k in sorted(key.items()):
        if k["run"] not in cache:
            cache[k["run"]] = json.loads((RAW / k["run"] / "results.json").read_text())
        res = cache[k["run"]]
        s = next(x for x in res["simulations"] if str(x["task_id"]) == str(k["task_id"]) and x.get("trial") == k.get("trial"))
        t = Task.model_validate(next(x for x in res["tasks"] if str(x["id"]) == str(k["task_id"])))
        r = judge_run(client, model, policy, t, s["messages"], meta.get(str(k["task_id"]), {}))
        tot += r["cost_usd"]; out[aid] = r
    d = ROOT / "study3_sealed" / "judge_validation"; d.mkdir(parents=True, exist_ok=True)
    (d / f"{model}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"model": model, "n": len(out), "unparsed": sum(r["verdict"] is None for r in out.values()),
                      "cost_usd": round(tot, 4)}))


if __name__ == "__main__":
    main(sys.argv[1])
