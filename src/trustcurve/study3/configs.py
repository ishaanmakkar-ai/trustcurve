"""Study 3 configuration roster (STUDY3.md §B′1) and the sealed-fault interface (§B′2).

20 configurations on tau2 airline. Planted flaws all sit on the base agent B0 (claude-haiku-5-5, full policy, no
harness). Each flaw source has its own sealed directory ``study3_sealed/<source>/`` holding ``fault_impl.py`` and
``params.json``; the analyst never opens them before the blind analysis (D′) is committed.

Sealed-module interface (extends Study 2's):
  apply(cfg_id, msg, state, toolkit, task_id) -> AssistantMessage       (required)
  policy(cfg_id, policy_text) -> policy_text                            (optional; knowledge-edit faults)
  logging: one JSON line per opportunity to $TC3_FAULT_LOG with event "draw" and fired bool; "applied" lines extra.

The Study 2 agent machinery (persona/harness/knowledge/fault hook) is reused unchanged: ``make_factory3`` builds a
Study 2 ``Config`` and swaps in the Study 3 fault loader and policy document around Study 2's ``make_factory``.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from pathlib import Path

from trustcurve.study2 import configs as c2

ROOT = Path(__file__).resolve().parents[3]
SEALED = Path(os.environ.get("TC3_SEALED_DIR", ROOT / "study3_sealed"))
POLICY_DIR = ROOT / "tasks" / "study3" / "policies"
HAIKU, HAIKU4, SONNET = "anthropic/claude-haiku-5-5", "anthropic/claude-haiku-4-5-20251001", "anthropic/claude-sonnet-5-5"
LUNA = "openai/responses/gpt-6-luna"
SOURCES = ("clean", "designed", "external", "mechanical", "natural")


@dataclass(frozen=True)
class Config3:
    id: str
    source: str
    model: str = HAIKU
    harness: str = "plain"               # plain | policy_check
    fault_source: str | None = None      # designed | external | mechanical (sealed module directory)
    policy_doc: str | None = None        # file under tasks/study3/policies/ replacing the tau2 policy (natural N3/N4)
    designer_known: bool = False         # Study 2 flaw types: analysed separately, excluded from H2
    study2_exposed: bool = False         # appeared in Study 2's results: H2 reported with and without
    card: dict = field(default_factory=dict, hash=False, compare=False)


def _card(model, guardrail=False, policy_version="Airline policy, current revision"):
    vendor, name = model.split("/")[0], model.split("/")[-1]
    tier = {"claude-sonnet-5-5": "frontier", "claude-haiku-5-5": "mid", "claude-haiku-4-5-20251001": "small",
            "gpt-6-luna": "small", "gpt-4o-mini-2024-07-18": "small"}.get(name, "mid")
    return {"model_vendor": vendor, "model": name, "tier": tier, "money_tools": True, "human_approval": False,
            "guardrail": guardrail, "policy_version": policy_version}


# N4 (STUDY3.md §B′1): the $0 model-list check on the Hexa key (2026-10-22) found older/smaller tool-capable OpenAI
# models; chosen: gpt-4o-mini-2024-07-18 (2024 small model, 128k context). gpt-3.5-turbo is older but its 16k context
# risks truncating tau2 conversations (implementation choice, labelled in STUDY3.md).
N4_MODEL = "openai/gpt-4o-mini-2024-07-18"
N4_POLICY = None

CONFIGS3 = {c.id: c for c in [
    Config3("C0", "clean", card=_card(HAIKU)),
    Config3("C1", "clean", card=_card(HAIKU)),
    Config3("C2", "clean", harness="policy_check", card=_card(HAIKU, guardrail=True)),
    Config3("C3", "clean", model=SONNET, card=_card(SONNET)),
    *[Config3(f"D{k}", "designed", fault_source="designed", card=_card(HAIKU)) for k in range(1, 5)],
    *[Config3(f"X{k}", "external", fault_source="external", card=_card(HAIKU)) for k in range(1, 5)],
    *[Config3(f"M{k}", "mechanical", fault_source="mechanical", card=_card(HAIKU)) for k in range(1, 5)],
    Config3("N1", "natural", model=HAIKU4, designer_known=True, card=_card(HAIKU4)),
    Config3("N2", "natural", model=LUNA, study2_exposed=True, card=_card(LUNA)),
    Config3("N3", "natural", policy_doc="tau_bench_v1_airline.md", card=_card(HAIKU, policy_version="Airline policy, earlier revision (since superseded)")),
    Config3("N4", "natural", model=N4_MODEL, policy_doc=N4_POLICY,
            card=_card(N4_MODEL, policy_version="Airline policy, earlier revision (since superseded)" if N4_POLICY else "Airline policy, current revision")),
]}

H2_SET = [c.id for c in CONFIGS3.values() if c.source in ("external", "mechanical", "natural") and not c.designer_known]
H2_SET_STRICT = [i for i in H2_SET if not CONFIGS3[i].study2_exposed]


def load_fault_module(source: str, sealed_dir: Path | None = None):
    d = Path(sealed_dir or SEALED) / source
    spec = importlib.util.spec_from_file_location(f"tc3_fault_{source}", d / "fault_impl.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def make_factory3(cfg: Config3, sealed_dir: Path | None = None):
    """Study 2's factory with (a) the Study 3 sealed module as the fault hook and (b) optional policy replacement
    (natural outdated document) or policy edit (sealed module's ``policy``)."""
    fault_mod = load_fault_module(cfg.fault_source, sealed_dir) if cfg.fault_source else None
    base = c2.Config(cfg.id, model=cfg.model, harness=cfg.harness, factor=cfg.source, fault=fault_mod is not None)
    orig = c2._load_fault_module
    try:
        c2._load_fault_module = lambda: fault_mod
        inner = c2.make_factory(base)
    finally:
        c2._load_fault_module = orig
    doc = (POLICY_DIR / cfg.policy_doc).read_text() if cfg.policy_doc else None
    edit = getattr(fault_mod, "policy", None) if fault_mod is not None else None

    def factory(tools, domain_policy, **kwargs):
        pol = doc if doc is not None else domain_policy
        if edit is not None:
            pol = edit(cfg.id, pol)
        return inner(tools, pol, **kwargs)

    return factory


def register3(cfg_id: str, sealed_dir: Path | None = None) -> str:
    from tau2.registry import registry
    name = f"tc3_{cfg_id}"
    if registry.get_agent_factory(name) is None:
        registry.register_agent_factory(make_factory3(CONFIGS3[cfg_id], sealed_dir), name)
    return name
