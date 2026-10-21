#!/usr/bin/env bash
# Run one Study 2 batch end to end: tau2 runs -> collect2 CSV -> spend ledger (stop rule enforced).
# Usage: run_batch.sh <phase> <name> <config> <tasks.json> <meta.json> <sim_llm> <sim_label> [ids_file]
# Env: CONC (default 6). Raw output: results/raw/study2/<name> (symlinked to the external drive). Keys via with_keys.sh.
set -uo pipefail
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
PHASE="$1"; NAME="$2"; CFG="$3"; TASKS="$4"; META="$5"; SIM="$6"; SIML="$7"; IDS="${8:-}"
PY="$HOME/.local/share/trustcurve/.venv/bin/python"
OUT="$R/results/raw/study2/$NAME"; LOG="$R/results/study2/logs/$NAME.log"; mkdir -p "$R/results/study2/logs" "$R/results/study2/runs"
ARGS=(--config "$CFG" --tasks "$TASKS" --user-llm "$SIM" --trials 1 --conc "${CONC:-6}" --out "$OUT")
[[ -n "$IDS" ]] && ARGS+=(--task-ids-file "$IDS")
for attempt in 1 2 3; do
  PYTHONDONTWRITEBYTECODE=1 "$R/scripts/with_keys.sh" "$PY" "$R/scripts/study2/run_config.py" "${ARGS[@]}" >> "$LOG" 2>&1 && break
  echo "attempt $attempt failed; resuming from checkpoint" >> "$LOG"; sleep 20
done
SUM=$(PYTHONPATH="$R/src" "$PY" -m trustcurve.study2.collect2 "$OUT/results.json" "$META" "$CFG" "$SIML" "$R/results/study2/runs/$NAME.csv" 2>>"$LOG" | tail -1)
echo "$SUM" >> "$LOG"
COST=$(echo "$SUM" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["cost_usd"])')
RUNS=$(echo "$SUM" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["runs"])')
"$PY" "$R/scripts/study2/spend.py" "$PHASE" "$NAME" "$RUNS" "$COST" "$CFG x $SIML" | tee -a "$LOG"
exit ${PIPESTATUS[0]}
