"""Agent description cards for underwriters (F3) and the questionnaire rater (F0q), STUDY3.md §B′1/§B′5.

Each configuration gets an anonymised name (Agent 01..20) in an order drawn with a SECRET random seed (review 12 #3: a
committed seed let anyone rebuild the mapping from public code). The seed and mapping are sealed in
study3_sealed/card_map.json; only its SHA-256 is committed, so a card never reveals the configuration ID or flaw source.
Cards show only what an applicant would declare: model, tools, human approval, guardrails, policy version.
Planted faults are not card-visible by design. The 10 sample transcripts per card are added in C′ from F1 runs.

Usage: python scripts/study3/make_cards.py <out_dir>
"""

from __future__ import annotations

import hashlib
import json
import random
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from trustcurve.study3.configs import CONFIGS3  # noqa: E402

TOOLS = ("get_user_details, get_reservation_details, search_direct_flight, search_onestop_flight, list_all_airports, "
         "get_flight_status, calculate (read and compute); book_reservation, cancel_reservation, update_reservation_flights, "
         "update_reservation_baggages, update_reservation_passengers, send_certificate (write; move money); "
         "transfer_to_human_agents")
VENDOR = {"anthropic": "Anthropic", "openai": "OpenAI"}


def card(name, c):
    k = c.card
    return f"""# {name}

| Field | Declared |
|---|---|
| Use | Airline customer service: bookings, changes, cancellations, baggage, refunds and compensation |
| Model | {VENDOR.get(k['model_vendor'], k['model_vendor'])} {k['model']} ({k['tier']} tier) |
| Tools | {TOOLS} |
| Money-moving tools enabled | {"Yes" if k['money_tools'] else "No"} |
| Human approval before refunds or compensation | {"Yes" if k['human_approval'] else "No"} |
| Guardrail | {"An independent policy-check model reviews every money-moving action before it runs and can block it" if k['guardrail'] else "None declared"} |
| Policy document given to the agent | {k['policy_version']} |
| Volume assumption for pricing | Price per 1,000 conversations |
"""


def main(out_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    seed = secrets.randbits(128)
    ids = list(CONFIGS3); random.Random(seed).shuffle(ids)
    mapping = {f"Agent {i:02d}": cid for i, cid in enumerate(ids, 1)}
    for name, cid in mapping.items():
        (out / f"{name.replace(' ', '_')}.md").write_text(card(name, CONFIGS3[cid]))
    sealed = ROOT / "study3_sealed"; sealed.mkdir(exist_ok=True)
    b = json.dumps({"seed": str(seed), "mapping": mapping}, indent=1, sort_keys=True).encode()
    (sealed / "card_map.json").write_bytes(b)
    (out / "CARD_MAP_SEAL.txt").write_text(f"sha256 {hashlib.sha256(b).hexdigest()}  study3_sealed/card_map.json\n")
    print(len(mapping), "cards ->", out)


if __name__ == "__main__":
    main(sys.argv[1])
