# TrustCurve

**How many runs before you can insure an AI agent?**

TrustCurve turns repeated runs of an AI agent into an insurable risk estimate: a failure rate with error bars, the number of runs needed to trust it, an expected dollar loss, and an indicative premium.

Status: **pilot** (τ²-bench airline domain). See `PILOT_PLAN.md`, `RESEARCH.md`, `ITERATIONS.md` and `PILOT.md` as they appear.

This is research code, not an insurance product or pricing advice.

## Environment (pilot)
- tau2-bench **v2.0.0** (`sierra-research/tau2-bench`, commit `57e5414`). τ³-bench was the previous release (v1.0). It's installed in a venv outside this repo using Python 3.12.
- All model roles (agent, user simulator, communicate judge) use `anthropic/claude-haiku-5-5` at provider-default sampling, because Haiku 5.5 rejects non-default temperature.
- Run: `TASKS="7 8" TRIALS=3 OUT=results/raw/<name> scripts/run_pilot.sh`. The API key is read from `~/.config/trustcurve/env`.
