#!/usr/bin/env bash
# Phase B loop 1 runs (STUDY2.md B-L1): screening of post-screening configs + date-repaired OpenAI simulator re-pilot.
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
V1T=tasks/study2/experience_v1/tasks.json; V1M=tasks/study2/experience_v1/meta.json
UWT=tasks/study2/underwriting/pool.json; UWM=tasks/study2/underwriting/meta.json
S45=tasks/study2/underwriting/screen_ids.txt; S30=tasks/study2/underwriting/screen30_ids.txt
H=anthropic/claude-haiku-5-5
{
echo "pilotD-B0-L B0 $V1T $V1M openai/gpt-6-luna L - 1"
echo "pilotD-B0-O B0 $V1T $V1M openai/gpt-6.1-sol O - 1"
echo "pilotD-B0-H B0 $V1T $V1M $H H - 1"
for C in KNO-WC KNO-WI KNO-WB KB-HPC KB-HCF KB-PPL KB-PST; do echo "uw1-$C $C $UWT $UWM $H H $S45 0"; done
echo "uw1-KB-CAPS KB-CAPS $UWT $UWM $H H $S30 0"
} > results/study2/phaseB_L1_batches.txt
rm -f results/study2/STOP_FLAG
run_one() {
  set -- $1
  [[ -f "$R/results/study2/STOP_FLAG" ]] && { echo "skip $1"; return; }
  IDS="$7"; [[ "$IDS" == "-" ]] && IDS=""
  DATE_HINT="$8" CONC=4 "$R/scripts/study2/run_batch.sh" B "$1" "$2" "$3" "$4" "$5" "$6" $IDS > /dev/null 2>&1
  rc=$?; [[ $rc -eq 3 ]] && touch "$R/results/study2/STOP_FLAG"
  echo "$1 rc=$rc $(tail -1 "$R/results/study2/logs/$1.log")"
}
export -f run_one; export R
cat results/study2/phaseB_L1_batches.txt | xargs -P 4 -I{} bash -c 'run_one "{}"'
echo PHASEB_L1_DONE
