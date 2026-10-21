"""Build the Study 2 underwriting pool (STUDY2.md S0/B4): tau2-Bench-Verified airline (50) + E3 refusal (40).

Writes tasks/study2/underwriting/{pool.json, meta.json, screen_ids.txt, rest_ids.txt, SOURCE.md}.
Metadata is derived mechanically (no outcomes): stratum = stratum_of(reason_for_call),
requester = the user id in the scenario, cancel_reason_category = keyword rule on the scenario text.
Screening half = stratified 45 of 90 (seed 20261021), per STUDY2.md §B4.

Usage: python scripts/study2/build_underwriting.py <verified_tasks.json>
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

REASON_RULES = [("health", r"\b(sick|ill|illness|health|medical|hospital|surgery|injur|doctor|covid|flu)"),
                ("weather", r"\b(weather|storm|hurricane|snow|blizzard)"),
                ("airline_cancelled", r"(airline cancel|flight (was|got|has been) cancel|cancelled by the airline)")]


STRATUM_RULES = [("book", r"\b(book (a|an|one|the|new)|to book|make a reservation|fly from|want to fly)\b"),
                 ("cancel", r"(\bcancel|booked (two|multiple))"),
                 ("change", r"\b(change|upgrade|downgrade|modif|push back|remove passenger|remove a passenger|bags?|suitcase)")]


def stratum_of(reason_for_call: str) -> str:
    """Customer's primary request from reason_for_call only: compensation/complaint wording wins; otherwise the
    earliest-mentioned of book / cancel / change; else other. (Replaces collect.request_type, which put every
    compensation complaint into 'cancel'; fixed before any Study 2 run.)"""
    t = (reason_for_call or "").lower()
    if re.search(r"(compensat|complain|delayed|voucher|unhappy about|refund for the insurance)", t):
        return "compensation"
    hits = [(m.start(), h) for h, pat in STRATUM_RULES for m in [re.search(pat, t)] if m]
    return min(hits)[1] if hits else "other"


# Review 6 #3: hand labels from the scenario text only (no outcomes), 2026-10-21. The keyword rule labelled
# "you do NOT have a health issue" as health and defaulted every unstated reason to change_of_plan.
# Covered reasons under the policy are the passenger's own health or weather; others' illness -> other;
# unstated or ambiguous -> unknown (an insured cancellation then scores 'uncertain', outside the primary total).
HAND_REASONS = {"V-7": "health", "V-19": "health", "V-49": "health", "V-29": "none", "V-31": "other",
                "V-32": "other", "V-36": "other", "V-43": "change_of_plan", "V-44": "change_of_plan",
                "V-45": "unknown", "V-9": "unknown", "V-37": "unknown", "V-24": "unknown"}


def reason_category(text: str) -> str:
    t = text.lower()
    for cat, pat in REASON_RULES:
        if re.search(pat, t):
            return cat
    return "change_of_plan" if "cancel" in t else "none"


def main(verified_path):
    from loguru import logger
    logger.remove()
    from tau2.data_model.tasks import Task
    from trustcurve.taskgen import task_user_id

    ver = json.loads(Path(verified_path).read_text())
    e3 = json.loads((ROOT / "tasks" / "e3_refusal.json").read_text())
    pool, meta = [], {}
    for src, prefix, tasks in (("tau2-bench-verified", "V", ver), ("e3_refusal", "", e3)):
        for t in tasks:
            t = json.loads(json.dumps(t))
            t["id"] = f"{prefix}-{t['id']}" if prefix else str(t["id"])
            t.pop("annotations", None)
            task = Task.model_validate(t)
            ins = t["user_scenario"]["instructions"]
            text = " ".join(str(ins.get(k) or "") for k in ("reason_for_call", "task_instructions", "known_info"))
            meta[t["id"]] = {"source": src, "stratum": stratum_of(ins.get("reason_for_call")),
                             "requester_user_id": task_user_id(t),
                             "cancel_reason_category": HAND_REASONS.get(t["id"], reason_category(text))}
            pool.append(t)
    out = ROOT / "tasks" / "study2" / "underwriting"; out.mkdir(parents=True, exist_ok=True)
    (out / "pool.json").write_text(json.dumps(pool, indent=1))
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    rng = random.Random(20261021); screen = []; by = {}
    for tid, m in meta.items():
        by.setdefault(m["stratum"], []).append(tid)
    odd = []
    for h in sorted(by):
        ids = sorted(by[h]); rng.shuffle(ids); by[h] = ids
        screen += ids[: len(ids) // 2]
        if len(ids) % 2:
            odd.append(h)
    rng.shuffle(odd)
    for h in odd[: 45 - len(screen)]:
        screen.append(by[h][len(by[h]) // 2])
    screen = sorted(screen)
    rest = sorted(set(meta) - set(screen))
    (out / "screen_ids.txt").write_text("\n".join(screen) + "\n")
    (out / "rest_ids.txt").write_text("\n".join(rest) + "\n")
    sha = hashlib.sha256(Path(verified_path).read_bytes()).hexdigest()
    (out / "SOURCE.md").write_text(
        "# Underwriting pool sources\n\n"
        f"- tau2-Bench-Verified airline tasks.json: github.com/amazon-agi/tau2-bench-verified (MIT), commit a470e45, "
        f"sha256 {sha}. Ids prefixed `V-`. Same DB and policy as tau2 v2.0.0.\n"
        "- E3 refusal tasks: tasks/e3_refusal.json (Goal 3 v2).\n")
    from collections import Counter
    print(json.dumps({"n": len(pool), "strata": Counter(m["stratum"] for m in meta.values()),
                      "screen": len(screen), "screen_strata": Counter(meta[i]["stratum"] for i in screen),
                      "reasons": Counter(m["cancel_reason_category"] for m in meta.values()),
                      "no_requester": [k for k, m in meta.items() if not m["requester_user_id"]]}, indent=0, default=str))


if __name__ == "__main__":
    main(sys.argv[1])
