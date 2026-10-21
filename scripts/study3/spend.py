"""Study 3 spend ledger and guard (STUDY3.md "Budget decision", Ishaan 2026-10-21).

Same method as Study 2 (results/study2/spend.csv): one row per batch, cost from tau2 per-message costs plus logged
judge/harness usage. Study 3 spend only; Study 2's $373.63 is not counted.

  python scripts/study3/spend.py check <phase> <projected_usd>          exit 3 if it would breach the gate or the cap
  python scripts/study3/spend.py add <phase> <batch> <runs> <cost_usd> [note]   append; exit 3 if a rule is breached

Rules: stop and ask at cumulative >= $540 (gate); never start a call that could pass $600 (hard cap);
stop and ask if a phase exceeds 1.5x its budget.
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

P = Path(__file__).resolve().parents[2] / "results" / "study3" / "spend.csv"
GATE, CAP = 540.0, 600.0
BUDGET = {"B": 15.0, "C": 440.0, "D": 15.0}
HEAD = ["timestamp", "phase", "batch", "runs", "cost_usd", "cumulative_study3_usd", "note"]


def rows():
    if not P.exists():
        P.parent.mkdir(parents=True, exist_ok=True)
        with open(P, "w", newline="") as f:
            csv.writer(f).writerow(HEAD)
        return []
    return list(csv.DictReader(open(P)))


def totals(rs, phase):
    cum = float(rs[-1]["cumulative_study3_usd"]) if rs else 0.0
    return cum, sum(float(r["cost_usd"]) for r in rs if r["phase"] == phase)


def main(argv):
    rs = rows()
    if argv[0] == "check":
        phase, proj = argv[1], float(argv[2])
        cum, ph = totals(rs, phase)
        print(f"study3 ${cum:.2f}; phase {phase} ${ph:.2f} of ${BUDGET.get(phase, 0):.0f}; projected +${proj:.2f}")
        if cum >= GATE or cum + proj > CAP or (phase in BUDGET and ph + proj > 1.5 * BUDGET[phase]):
            print("STOP AND ASK: gate, cap or phase rule would be breached"); return 3
        return 0
    phase, batch, runs, cost = argv[1], argv[2], int(argv[3]), float(argv[4])
    note = argv[5] if len(argv) > 5 else ""
    cum, ph = totals(rs, phase)
    cum += cost; ph += cost
    with open(P, "a", newline="") as f:
        csv.writer(f).writerow([datetime.now().isoformat(timespec="minutes"), phase, batch, runs, f"{cost:.4f}", f"{cum:.2f}", note])
    print(f"study3 ${cum:.2f}; phase {phase} ${ph:.2f} of ${BUDGET.get(phase, 0):.0f}")
    if cum >= GATE or (phase in BUDGET and ph > 1.5 * BUDGET[phase]):
        print("STOP AND ASK: spend rule breached"); return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
