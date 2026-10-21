#!/usr/bin/env bash
# Re-collect Study 2 batches from raw results with the current collector/ledger (no API calls).
# Usage: recollect.sh <batch-name> <meta.json> <config> <sim_label>
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
PYTHONPATH="$R/src" "$HOME/.local/share/trustcurve/.venv/bin/python" -m trustcurve.study2.collect2 \
  "$R/results/raw/study2/$1/results.json" "$2" "$3" "$4" "$R/results/study2/runs/$1.csv" 2>/dev/null | tail -1
