#!/usr/bin/env bash
# Reference run (EXPERIMENTS.md): REF-H all 50 tasks x 20 (Haiku agent + Haiku simulator) and
# REF-S 25 breadth tasks x 20 (Haiku agent + Sonnet simulator), run side by side (2 arms at concurrency 8).
# Rate-limit plan (PILOT.md): on any 429, halve the concurrency and resume into the same output (auto_resume).
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"
run() {  # name user agent trials tasks
  local c=8 i=0 L="$R/results/logs/$1.log"
  while :; do
    CONC=$c "$R/scripts/run_arm.sh" "$1" "$2" "$3" "$4" "$5"
    if grep -q -E "RateLimitError|rate_limit_error|Error code: 429" "$L" && (( c > 1 )); then
      mv "$L" "$R/results/logs/$1.conc$c-part$i.log"; c=$(( c / 2 )); i=$(( i + 1 ))
    else break; fi
  done
}
run ref-H anthropic/claude-haiku-5-5 anthropic/claude-haiku-5-5 20 "ids:$(seq -s ' ' 0 49)" &
run ref-S anthropic/claude-sonnet-5-5 anthropic/claude-haiku-5-5 20 "ids:$(cat "$R/results/pilot/breadth_tasks.txt")" &
wait
echo "REF_DONE $(date)" > "$R/results/logs/queue_ref.done"
