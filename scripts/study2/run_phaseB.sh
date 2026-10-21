#!/usr/bin/env bash
# Phase B paid runs (STUDY2.md B3/B4): fidelity pilot on burned v1 tasks + screening (first half of underwriting).
# 4 batches in parallel (CONC=4 each). A spend-guard breach (exit 3) stops further launches.
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
V1T=tasks/study2/experience_v1/tasks.json; V1M=tasks/study2/experience_v1/meta.json
UWT=tasks/study2/underwriting/pool.json; UWM=tasks/study2/underwriting/meta.json
S45=tasks/study2/underwriting/screen_ids.txt; S30=tasks/study2/underwriting/screen30_ids.txt
H=anthropic/claude-haiku-5-5
{
echo "pilot-B0-H B0 $V1T $V1M $H H -"
echo "pilot-PER-PL-H PER-PL $V1T $V1M $H H -"
echo "pilot-KNO-WR-H KNO-WR $V1T $V1M $H H -"
echo "pilot-B0-L B0 $V1T $V1M openai/gpt-6-luna L -"
echo "pilot-B0-O B0 $V1T $V1M openai/gpt-6.1-sol O -"
for C in B0 PER-PL PER-ST PER-FA HAR-PC HAR-CF KNO-RM KNO-WR INT-1 INT-3; do echo "uw1-$C $C $UWT $UWM $H H $S45"; done
for C in CAP-S CAP-O INT-2; do echo "uw1-$C $C $UWT $UWM $H H $S30"; done
} > results/study2/phaseB_batches.txt
touch results/study2/STOP_FLAG; rm -f results/study2/STOP_FLAG
run_one() {
  set -- $1
  [[ -f "$R/results/study2/STOP_FLAG" ]] && { echo "skip $1"; return; }
  IDS="$7"; [[ "$IDS" == "-" ]] && IDS=""
  CONC=4 "$R/scripts/study2/run_batch.sh" B "$1" "$2" "$3" "$4" "$5" "$6" $IDS > /dev/null 2>&1
  rc=$?; [[ $rc -eq 3 ]] && touch "$R/results/study2/STOP_FLAG"
  echo "$1 rc=$rc $(tail -1 "$R/results/study2/logs/$1.log")"
}
export -f run_one; export R
cat results/study2/phaseB_batches.txt | xargs -P 4 -I{} bash -c 'run_one "{}"'
echo PHASEB_DONE
