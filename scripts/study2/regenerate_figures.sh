#!/usr/bin/env bash
# Regenerate every Study 2 figure from committed code and committed results (no API calls).
set -euo pipefail
R="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$R"; PY="${PY:-$HOME/.local/share/trustcurve/.venv/bin/python}"
"$PY" scripts/study2/fig_phaseA.py results/study2/phaseA/grid_loop2.json results/study2/phaseA/
"$PY" scripts/study2/fig_phaseA3.py results/study2/phaseA/grid_loop3.json results/study2/phaseA/
"$PY" scripts/study2/fig_phaseC.py results/study2/forecasts_frozen.json results/study2/phaseC/score_c.json results/study2/phaseC/
"$PY" scripts/study2/fig_phaseC_v2.py results/study2/phaseC/
