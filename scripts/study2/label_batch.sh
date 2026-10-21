#!/usr/bin/env bash
# Label one Study 2 batch with the Goal 3 RUBRICS labeller (Haiku); cost recorded in the spend ledger.
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"; N="$1"; PHASE="${2:-B}"
OUT="$R/results/study2/labels/$N.csv"
J=$(PYTHONPATH="$R/src" "$R/scripts/with_keys.sh" "$HOME/.local/share/trustcurve/.venv/bin/python" "$R/scripts/label_runs.py" \
    "$R/results/raw/study2/$N/results.json" "$R/results/study2/runs/$N.csv" "$OUT" 2>>"$R/results/study2/logs/label-$N.log" | tail -1)
echo "$J" >> "$R/results/study2/logs/label-$N.log"
C=$(echo "$J" | "$HOME/.local/share/trustcurve/.venv/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["label_cost_usd"])')
L=$(echo "$J" | "$HOME/.local/share/trustcurve/.venv/bin/python" -c 'import json,sys; print(json.load(sys.stdin)["labelled"])')
"$HOME/.local/share/trustcurve/.venv/bin/python" "$R/scripts/study2/spend.py" "$PHASE" "labels-$N" "$L" "$C" "labeller" ; echo "labels $N: $J"
