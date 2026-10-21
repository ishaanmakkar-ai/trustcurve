#!/usr/bin/env bash
# Live 1-task smoke test of every non-planted configuration (review 6 #1). Phase B spend.
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
echo V-48 > "$R/results/study2/smoke_ids.txt"
for C in B0 HAR-CF HAR-PC CAP-O CAP-S CAP-X PER-PL PER-ST PER-FA KNO-RM KNO-WR INT-1 INT-2 INT-3; do
  CONC=1 "$R/scripts/study2/run_batch.sh" B "smoke-$C" "$C" tasks/study2/underwriting/pool.json tasks/study2/underwriting/meta.json anthropic/claude-haiku-5-5 H "$R/results/study2/smoke_ids.txt" || { echo "STOP $C"; exit 3; }
done
echo SMOKE_DONE
