"""Statement-judge pass over C′ runs via the Message Batches API (STUDY3.md §C′5; judge.py), behind the spend guard.

For every run in results/study3/runs/<prefix>*.csv not yet judged: build the judge prompt from the raw transcript, submit
as one batch, poll until it ends, collect, re-submit unparsed verdicts once, record the cost (phase C). Totals (no
quotes) go to results/study3/judge/<prefix>_<model>.json keyed "config|task_id|trial"; full verdicts go to
results/raw/study3/judge/ (external drive). Run via scripts/with_keys.sh.

Usage: python scripts/study3/judge_batch.py <prefix: uw-|exp-> <model> [--dry] [--limit N] [--phase C]
"""

from __future__ import annotations

import csv
import glob
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
PER_CONV = {"claude-haiku-5-5": 0.0008 * 0.5, "claude-sonnet-5-5": 0.0166 * 0.5}   # batch price, measured/estimated
MARGIN = 1.5


def meta_for(batch):
    if batch.startswith("uw-F1-"):
        return ROOT / "tasks/study2/underwriting/meta.json"
    if batch.startswith("uw-F2-"):
        return ROOT / "tasks/study3/F2/meta.json"
    return ROOT / "tasks/study3_sealed/meta.json"


def main(prefix, model, dry=False, limit=None, phase="C"):
    import anthropic
    from loguru import logger
    from tau2.data_model.tasks import Task
    from tau2.registry import registry

    from trustcurve.study3 import judge as J
    logger.remove()
    out_p = ROOT / "results/study3/judge" / f"{prefix.rstrip('-')}_{model}.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    done = json.loads(out_p.read_text()) if out_p.exists() else {}
    raw_dir = ROOT / "results/raw/study3/judge"; raw_dir.mkdir(parents=True, exist_ok=True)
    policy = registry.get_env_constructor("airline")().get_policy()
    items, index = [], {}
    for f in sorted(glob.glob(str(ROOT / "results/study3/runs" / f"{prefix}*.csv"))):
        batch = Path(f).stem
        R = json.loads((ROOT / "results/raw/study3" / batch / "results.json").read_text())
        sims = {(str(s["task_id"]), str(s.get("trial"))): s for s in R["simulations"]}
        tasks = {str(t["id"]): t for t in R["tasks"]}
        meta = json.loads(meta_for(batch).read_text())
        for r in csv.DictReader(open(f)):
            k = f"{r['config']}|{r['task_id']}|{r['trial']}"
            if r.get("error") or k in done:
                continue
            s = sims[(r["task_id"], str(r["trial"]))]
            system, user = J.prompt(policy, Task.model_validate(tasks[r["task_id"]]), s["messages"], meta.get(r["task_id"], {}))
            cid = f"j{len(items):06d}"
            items.append((cid, system, user)); index[cid] = k
    if limit:
        items = items[:limit]
    proj = len(items) * PER_CONV[model] * MARGIN
    print(json.dumps({"to_judge": len(items), "already": len(done), "projected_usd": round(proj, 2)}))
    if dry or not items:
        return 0
    if subprocess.call([sys.executable, str(ROOT / "scripts/study3/spend.py"), "check", phase, f"{proj:.2f}"]) != 0:
        return 3
    client = anthropic.Anthropic()
    total_cost, pending, note = 0.0, items, ""
    for attempt in range(2):
        results = {}
        for i in range(0, len(pending), 10000):
            chunk = pending[i:i + 10000]
            bid = J.batch_submit(client, model, chunk, note)
            while client.messages.batches.retrieve(bid).processing_status != "ended":
                time.sleep(60)
            results |= J.batch_collect(client, model, bid)
        total_cost += sum(v["cost_usd"] for v in results.values())
        for cid, v in results.items():
            if v["verdict"] is not None:
                done[index[cid]] = {"totals": v["totals"], "model": model}
                with open(raw_dir / f"{prefix.rstrip('-')}_{model}.jsonl", "a") as fh:
                    fh.write(json.dumps({"key": index[cid], "verdict": v["verdict"]}) + "\n")
        pending = [it for it in pending if results.get(it[0], {}).get("verdict") is None]
        note = J.RETRY_NOTE
        if not pending:
            break
    for it in pending:                                             # still unparsed after the retry: missing
        done[index[it[0]]] = {"totals": J.totals(None), "model": model}
    out_p.write_text(json.dumps(done, indent=0, sort_keys=True))
    subprocess.call([sys.executable, str(ROOT / "scripts/study3/spend.py"), "add", phase, f"judge-{prefix.rstrip('-')}-{model}",
                     str(len(items)), f"{total_cost:.4f}", f"statement judge via batch ({len(pending)} missing)"])
    print(json.dumps({"judged": len(items) - len(pending), "missing": len(pending), "cost_usd": round(total_cost, 4)}))
    return 0


if __name__ == "__main__":
    a = sys.argv
    lim = int(a[a.index("--limit") + 1]) if "--limit" in a else None
    ph = a[a.index("--phase") + 1] if "--phase" in a else "C"
    sys.exit(main(a[1], a[2], "--dry" in a, lim, ph))
