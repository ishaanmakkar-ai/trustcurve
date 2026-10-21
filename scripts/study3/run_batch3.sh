#!/usr/bin/env bash
# Run one Study 3 batch end to end: spend pre-check -> tau2 runs -> collect3 CSV -> spend ledger (gate/cap enforced).
# Usage: run_batch3.sh <phase> <name> <config> <tasks.json> <meta.json> <sim_llm> <sim_label> <projected_usd> [ids_file]
# Env: CONC (default 6), TRIALS (default 1), DATE_HINT=1. Raw output: results/raw/study3/<name>. Keys via with_keys.sh.
set -uo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$R"
PHASE="$1"; NAME="$2"; CFG="$3"; TASKS="$4"; META="$5"; SIM="$6"; SIML="$7"; PROJ="$8"; IDS="${9:-}"
PY="$HOME/.local/share/trustcurve/.venv/bin/python"
"$PY" "$R/scripts/study3/spend.py" check "$PHASE" "$PROJ" || { echo "spend guard: not starting $NAME"; exit 3; }
OUT="$R/results/raw/study3/$NAME"; LOG="$R/results/study3/logs/$NAME.log"; mkdir -p "$R/results/study3/logs" "$R/results/study3/runs"
ARGS=(--config "$CFG" --tasks "$TASKS" --user-llm "$SIM" --trials "${TRIALS:-1}" --conc "${CONC:-6}" --out "$OUT")
[[ -n "$IDS" ]] && ARGS+=(--task-ids-file "$IDS")
[[ "${DATE_HINT:-0}" == "1" ]] && ARGS+=(--date-hint)
[[ "${STOP_HINT:-0}" == "1" ]] && ARGS+=(--stop-hint)
for attempt in 1 2 3; do
  PYTHONPATH="$R/src" PYTHONDONTWRITEBYTECODE=1 "$R/scripts/with_keys.sh" "$PY" "$R/scripts/study3/run_config3.py" "${ARGS[@]}" >> "$LOG" 2>&1 && break
  echo "attempt $attempt failed; resuming from checkpoint" >> "$LOG"; sleep 20
done
SUM=$(PYTHONPATH="$R/src" "$PY" -m trustcurve.study3.collect3 "$OUT/results.json" "$META" "$CFG" "$SIML" "$R/results/study3/runs/$NAME.csv" 2>>"$LOG" | tail -1)
echo "$SUM" >> "$LOG"
COST=$(echo "$SUM" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["cost_usd"])')
RUNS=$(echo "$SUM" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["runs"])')
UNP=$(echo "$SUM" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("unpriced", 0))')
"$PY" "$R/scripts/study3/spend.py" add "$PHASE" "$NAME" "$RUNS" "$COST" "$CFG x $SIML" | tee -a "$LOG"
RC=${PIPESTATUS[0]}
if [[ "$UNP" != "0" ]]; then echo "STOP: $UNP unpriced runs in $NAME (spend undercounted); add the model's price" | tee -a "$LOG"; exit 4; fi
exit $RC
