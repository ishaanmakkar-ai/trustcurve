#!/usr/bin/env bash
# Phase C underwriting (STUDY2.md §C): remaining underwriting tasks per configuration, Haiku simulator, no date hint.
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
U=tasks/study2/underwriting; H=anthropic/claude-haiku-5-5
{
for C in B0 PER-PL PER-ST PER-FA HAR-PC HAR-CF KNO-RM KNO-WR INT-1 INT-3 KNO-WC KNO-WI KNO-WB KB-HPC KB-HCF KB-PPL KB-PST CAP-L CAP-H4 H4-KB KB-CAPS; do echo "uw2-$C $C $U/rest_ids.txt"; done
for C in CAP-S CAP-O INT-2; do echo "uw2-$C $C $U/rest60_ids.txt"; done
} > results/study2/phaseC_uw_batches.txt
rm -f results/study2/STOP_FLAG
run_one() {
  set -- $1
  [[ -f "$R/results/study2/STOP_FLAG" ]] && { echo "skip $1"; return; }
  CONC=4 "$R/scripts/study2/run_batch.sh" C "$1" "$2" "$R/tasks/study2/underwriting/pool.json" "$R/tasks/study2/underwriting/meta.json" anthropic/claude-haiku-5-5 H "$3" > /dev/null 2>&1
  rc=$?; [[ $rc -eq 3 ]] && touch "$R/results/study2/STOP_FLAG"
  echo "$1 rc=$rc $(tail -1 "$R/results/study2/logs/$1.log")"
}
export -f run_one; export R
cat results/study2/phaseC_uw_batches.txt | xargs -P 4 -I{} bash -c 'run_one "{}"'
echo PHASEC_UW_DONE
