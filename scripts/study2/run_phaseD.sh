#!/usr/bin/env bash
# Phase D runs (STUDY2.md §D): D1..D6 (sealed planted faults on B0) x 90 underwriting tasks, Haiku simulator.
# The sealed module is imported by path at runtime; the analyst does not open it.
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
U=tasks/study2/underwriting
rm -f results/study2/STOP_FLAG
run_one() {
  [[ -f "$R/results/study2/STOP_FLAG" ]] && { echo "skip $1"; return; }
  CONC=4 "$R/scripts/study2/run_batch.sh" D "d-$1" "$1" "$R/tasks/study2/underwriting/pool.json" "$R/tasks/study2/underwriting/meta.json" anthropic/claude-haiku-5-5 H > /dev/null 2>&1
  rc=$?; [[ $rc -eq 3 ]] && touch "$R/results/study2/STOP_FLAG"
  echo "d-$1 rc=$rc $(tail -1 "$R/results/study2/logs/d-$1.log")"
}
export -f run_one; export R
printf "D1\nD2\nD3\nD4\nD5\nD6\n" | xargs -P 3 -I{} bash -c 'run_one {}'
echo PHASED_DONE
