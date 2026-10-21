#!/usr/bin/env bash
# TrustCurve pilot: tau2-bench airline, N tasks x K trials, Anthropic-only.
# The key is read from ~/.config/trustcurve/env and never printed.
set -euo pipefail

TASKS="${TASKS:-}"            # space-separated task ids; required
TRIALS="${TRIALS:-3}"
SEED="${SEED:-20261021}"
MODEL="${MODEL:-anthropic/claude-haiku-5-5}"
CONC="${CONC:-3}"
OUT="${OUT:?set OUT to an output dir under results/raw/}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT";; esac  # tau2 resolves relative paths under its own data dir
VENV="${VENV:-$HOME/.local/share/trustcurve/.venv}"

[ -n "$TASKS" ] || { echo "TASKS is required" >&2; exit 2; }
set -a; . "$HOME/.config/trustcurve/env"; set +a

mkdir -p "$OUT"
# Haiku 5.5 rejects non-default sampling params, so pass empty llm args (provider defaults).
# Every model role, including the communicate judge, is Anthropic.
"$VENV/bin/tau2" run \
  --benchmark none --domain airline --agent llm_agent \
  --agent-llm "$MODEL" --agent-llm-args '{}' \
  --user-llm "$MODEL" --user-llm-args '{}' \
  --communicate-judge "{\"model\": \"$MODEL\", \"model_args\": {}}" \
  --task-ids $TASKS --num-trials "$TRIALS" --seed "$SEED" \
  --max-concurrency "$CONC" --save-to "$OUT" --log-level ERROR
