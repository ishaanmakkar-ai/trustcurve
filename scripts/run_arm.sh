#!/usr/bin/env bash
# Usage: run_arm.sh <name> <user_llm> <agent_llm> <trials> <tasks-json-or-"ids:..."> 
set -uo pipefail
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"
cd "$R"
NAME="$1"; USER_LLM="$2"; AGENT_LLM="$3"; TRIALS="$4"; SRC="$5"
LOG="$R/results/logs/$NAME.log"; mkdir -p "$R/results/logs"
if [[ "$SRC" == ids:* ]]; then ARGS=(--task-ids ${SRC#ids:}); else ARGS=(--tasks-json "$SRC"); fi
PYTHONDONTWRITEBYTECODE=1 "$R/scripts/with_keys.sh" "$HOME/.local/share/trustcurve/.venv/bin/python" "$R/scripts/run_tasks.py" \
  "${ARGS[@]}" --user-llm "$USER_LLM" --agent-llm "$AGENT_LLM" --trials "$TRIALS" --conc 8 \
  --out "$R/results/raw/$NAME" > "$LOG" 2>&1
echo "exit=$? name=$NAME" >> "$LOG"
