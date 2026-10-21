"""Blind structural check of the sealed fault modules (STUDY3.md §B′2): builds every planted configuration's agent
through ``make_factory3`` and calls ``apply`` on a neutral text message, printing only pass/fail per configuration.
Prints no module content, no policy text and no message text.

Usage: python scripts/study3/check_sealed.py [source ...]
"""

from __future__ import annotations

import os
import sys
import tempfile

from tau2.data_model.message import AssistantMessage
from tau2.registry import registry

from trustcurve.study3.configs import CONFIGS3, load_fault_module, make_factory3


def main(sources):
    env = registry.get_env_constructor("airline")()
    tools, pol = env.get_tools(), env.get_policy()
    os.environ["TC3_FAULT_LOG"] = tempfile.mktemp(suffix=".jsonl")
    ok = True
    for cid, cfg in CONFIGS3.items():
        if cfg.fault_source not in sources:
            continue
        try:
            agent = make_factory3(cfg)(tools, pol, llm=cfg.model, llm_args={})
            assert isinstance(agent.system_prompt, str) and len(agent.system_prompt) > 1000
            mod = load_fault_module(cfg.fault_source)
            out = mod.apply(cid, AssistantMessage(role="assistant", content="Thanks for waiting."), type("S", (), {"messages": []})(),
                            tools[0]._func.__self__, "check")
            assert isinstance(out, AssistantMessage)
            print(cid, "PASS")
        except Exception as e:  # noqa: BLE001
            ok = False
            print(cid, "FAIL", type(e).__name__)
    os.path.exists(os.environ["TC3_FAULT_LOG"]) and os.remove(os.environ["TC3_FAULT_LOG"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["external", "mechanical"]))
