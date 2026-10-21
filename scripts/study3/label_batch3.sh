#!/usr/bin/env bash
# Label one Study 3 batch with the Goal 3 RUBRICS labeller (Haiku); cost recorded in the Study 3 spend ledger.
# Usage: label_batch3.sh <batch_name> [phase]
R="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$R"; N="$1"; PHASE="${2:-B}"
PY="$HOME/.local/share/trustcurve/.venv/bin/python"
mkdir -p "$R/study3_sealed/labels" "$R/results/study3/logs"
"$PY" "$R/scripts/study3/spend.py" check "$PHASE" 0.5 || exit 3
J=$(PYTHONPATH="$R/src" "$R/scripts/with_keys.sh" "$PY" "$R/scripts/label_runs.py" \
    "$R/results/raw/study3/$N/results.json" "$R/results/study3/runs/$N.csv" "$R/study3_sealed/labels/$N.csv" 2>>"$R/results/study3/logs/label-$N.log" | tail -1)
echo "$J" >> "$R/results/study3/logs/label-$N.log"
C=$(echo "$J" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["label_cost_usd"])')
L=$(echo "$J" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["labelled"])')
"$PY" "$R/scripts/study3/spend.py" add "$PHASE" "labels-$N" "$L" "$C" "labeller"; echo "labels $N: $J"
