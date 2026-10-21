"""Study 2 configurations: knowledge variants, dry-run pricing, verdict parsing, harness blocking (no API calls)."""

import json

import pytest

tau2 = pytest.importorskip("tau2")

from trustcurve.study2 import configs as C  # noqa: E402


def env():
    from tau2.registry import registry
    e = registry.get_env_constructor("airline")()
    return e


def test_policy_variants():
    pol = env().get_policy()
    assert C.policy_variant(pol, "full") == pol
    rm = C.policy_variant(pol, "refund_removed")
    assert "certificate" not in rm.split("## Cancel flight")[1] and "5 to 7 business days" not in rm
    assert "## Cancel flight" in rm and "It is a business flight" in rm  # cancellation rules kept
    wr = C.policy_variant(pol, "wrong_rule")
    assert "last 72 hrs" in wr and "last 24 hrs" not in wr and len(wr) == len(pol)


def test_config_table():
    assert len(C.CONFIGS) == 14
    assert {c.factor for c in C.CONFIGS.values()} == {"base", "capability", "persona", "harness", "knowledge",
                                                      "interaction"}
    for c in C.CONFIGS.values():
        assert c.persona in C.PERSONAS


def test_dry_run_prices_cancellation_without_mutating():
    e = env(); tk = e.get_tools()[0]._func.__self__
    r = tk.db.reservations["VAAOXJ"]
    paid = sum(p.amount for p in r.payment_history)
    assert C._money_moved(tk, "cancel_reservation", {"reservation_id": "VAAOXJ"}) == pytest.approx(paid)
    assert tk.db.reservations["VAAOXJ"].status != "cancelled"  # live DB untouched
    assert C._money_moved(tk, "send_certificate", {"user_id": "lei_rossi_3206", "amount": 150}) == pytest.approx(150)
    assert C._money_moved(tk, "cancel_reservation", {"reservation_id": "NOPE00"}) == 0


def test_verdicts():
    assert C._verdict("APPROVE", "APPROVE", "REJECT")
    assert not C._verdict("REJECT: not eligible", "APPROVE", "REJECT")
    assert not C._verdict("I would REJECT this because ...", "APPROVE", "REJECT")
    assert C._verdict("CONFIRM", "CONFIRM", "CANCEL")
    assert not C._verdict("CANCEL: customer did not ask", "CONFIRM", "CANCEL")


def test_harness_blocks_then_allows(monkeypatch, tmp_path):
    """A REJECTed money call is returned to the agent as a tool error and never reaches the environment."""
    from tau2.data_model.message import AssistantMessage, ToolCall, UserMessage
    import tau2.utils.llm_utils as lu
    import tau2.agent.llm_agent as la

    calls = {"agent": 0, "check": 0}
    cancel = AssistantMessage(role="assistant", content=None, tool_calls=[
        ToolCall(id="c1", name="cancel_reservation", arguments={"reservation_id": "VAAOXJ"})])
    sorry = AssistantMessage(role="assistant", content="I can't cancel that booking.")

    def fake_generate(model, messages, tools=None, call_name=None, **kw):
        if call_name == "tc2_policy_check":
            calls["check"] += 1
            return AssistantMessage(role="assistant", content="REJECT: not refundable", usage={"prompt_tokens": 1})
        calls["agent"] += 1
        return cancel if calls["agent"] == 1 else sorry

    monkeypatch.setattr(lu, "generate", fake_generate)
    monkeypatch.setattr(la, "generate", fake_generate)
    monkeypatch.setattr(C, "generate", fake_generate, raising=False)
    monkeypatch.setenv("TC2_HARNESS_LOG", str(tmp_path / "h.jsonl"))
    import tau2.utils.llm_utils
    monkeypatch.setattr(tau2.utils.llm_utils, "generate", fake_generate)
    e = env()
    agent = C.make_factory(C.CONFIGS["HAR-PC"])(e.get_tools(), e.get_policy(), llm="anthropic/claude-haiku-5-5",
                                                llm_args={})
    st = agent.get_init_state()
    out, st = agent.generate_next_message(UserMessage(role="user", content="cancel VAAOXJ please"), st)
    assert out.content == "I can't cancel that booking." and not out.tool_calls
    assert calls["check"] == 1
    assert any(getattr(m, "role", "") == "tool" and m.error for m in st.messages)
    log = [json.loads(x) for x in (tmp_path / "h.jsonl").read_text().splitlines()]
    assert log[0]["allowed"] is False and log[0]["tool"] == "cancel_reservation"
    assert e.tools.db.reservations["VAAOXJ"].status != "cancelled"
