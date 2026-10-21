"""Append a batch's cost to results/study2/spend.csv and enforce the stop-and-ask rules.

Usage: python scripts/study2/spend.py <phase> <batch> <runs> <cost_usd> [note]
Exit code 3 if cumulative project spend passes $450 or the phase total exceeds 1.5x its budget.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

P = Path(__file__).resolve().parents[2] / "results" / "study2" / "spend.csv"
BUDGET = {"B": 40.0, "C": 250.0, "D": 40.0}
STOP_AT = 450.0

rows = list(csv.DictReader(open(P)))
cum = float(rows[-1]["cumulative_project_usd"]) if rows else 0.0
phase, batch, runs, cost = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
note = sys.argv[5] if len(sys.argv) > 5 else ""
cum += cost
with open(P, "a", newline="") as f:
    csv.writer(f).writerow([datetime.now().isoformat(timespec="minutes"), phase, batch, runs, f"{cost:.4f}", f"{cum:.2f}", note])
phase_tot = sum(float(r["cost_usd"]) for r in rows if r["phase"] == phase) + cost
print(f"cumulative ${cum:.2f}; phase {phase} ${phase_tot:.2f} of ${BUDGET.get(phase, 0):.0f}")
if cum > STOP_AT or (phase in BUDGET and phase_tot > 1.5 * BUDGET[phase]):
    print("STOP AND ASK: spend rule breached"); sys.exit(3)
