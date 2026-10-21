"""Study 3 roster and sealed-fault interface (STUDY3.md §B′1–B′2), with a stub module. No API calls."""

import textwrap

import pytest

tau2 = pytest.importorskip("tau2")

from trustcurve.study3 import configs as C  # noqa: E402

STUB = textwrap.dedent('''
    def apply(cfg_id, msg, state, toolkit, task_id):
        return msg
    def policy(cfg_id, text):
        return text + "\\nSTUB-EDIT " + cfg_id
''')


def env():
    from tau2.registry import registry
    return registry.get_env_constructor("airline")()


def stub_dir(tmp_path):
    for s in ("designed", "external", "mechanical"):
        d = tmp_path / s; d.mkdir()
        (d / "fault_impl.py").write_text(STUB); (d / "params.json").write_text("{}")
    return tmp_path


def test_roster_shape():
    cs = list(C.CONFIGS3.values())
    assert len(cs) == 20 and [c.id for c in cs][:4] == ["C0", "C1", "C2", "C3"]
    assert sum(c.source == "clean" for c in cs) == 4
    for s in ("designed", "external", "mechanical", "natural"):
        assert sum(c.source == s for c in cs) == 4
    assert len(C.H2_SET) == 11 and "N1" not in C.H2_SET and len(C.H2_SET_STRICT) == 10
    assert all(c.model == C.HAIKU for c in cs if c.fault_source)            # planted flaws all on B0
    assert {c.card["guardrail"] for c in cs if c.id != "C2"} == {False} and C.CONFIGS3["C2"].card["guardrail"]


def test_factories_build_and_apply_policy(tmp_path):
    d = stub_dir(tmp_path)
    e = env(); tools, pol = e.get_tools(), e.get_policy()
    for cid, cfg in C.CONFIGS3.items():
        agent = C.make_factory3(cfg, d)(tools, pol, llm=cfg.model, llm_args={})
        sp = agent.system_prompt
        if cfg.fault_source:
            assert f"STUB-EDIT {cid}" in sp
        elif cfg.policy_doc:
            assert "STUB-EDIT" not in sp and pol not in sp
            assert (C.POLICY_DIR / cfg.policy_doc).read_text().strip()[:200] in sp
        else:
            assert pol in sp and "STUB-EDIT" not in sp


def test_outdated_policy_is_genuinely_older():
    v1 = (C.POLICY_DIR / "tau_bench_v1_airline.md").read_text()
    cur = env().get_policy()
    assert v1 != cur and "Airline Agent Policy" in v1 and "refunds and compensation" not in v1.split("\n")[4]
