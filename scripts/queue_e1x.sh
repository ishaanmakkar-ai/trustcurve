#!/usr/bin/env bash
# Run E1x-SO, E1x-SS and phase-1b (breadth, refusal) one arm at a time, alongside the E2 -> E3 chain
# (two arms at concurrency 8 at once, as already run without error for E1-O + E2).
# Rate-limit plan (PILOT.md): on any 429, halve the concurrency and resume into the same output (auto_resume).
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"
B="ids:$(cat "$R/results/pilot/breadth_tasks.txt")"
run() {  # name user agent trials tasks
  local c=8 i=0 L="$R/results/logs/$1.log"
  while :; do
    CONC=$c "$R/scripts/run_arm.sh" "$1" "$2" "$3" "$4" "$5"
    if grep -q -E "RateLimitError|rate_limit_error|Error code: 429" "$L" && (( c > 1 )); then
      mv "$L" "$R/results/logs/$1.conc$c-part$i.log"; c=$(( c / 2 )); i=$(( i + 1 ))
    else break; fi
  done
}
run e1x-SO openai/gpt-6.1-sol anthropic/claude-sonnet-5-5 2 "$B"
run e1x-SS anthropic/claude-sonnet-5-5 anthropic/claude-sonnet-5-5 2 "$B"
run p1b-breadth anthropic/claude-haiku-5-5 anthropic/claude-sonnet-5-5 2 "$B"
run p1b-refusal anthropic/claude-haiku-5-5 anthropic/claude-sonnet-5-5 1 "$R/tasks/e3_refusal.json"
echo "QUEUE_DONE $(date)" > "$R/results/logs/queue_e1x.done"
