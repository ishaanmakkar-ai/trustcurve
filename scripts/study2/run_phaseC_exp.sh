#!/usr/bin/env bash
# Phase C experience runs (STUDY2.md §C). Refuses to start unless results/study2/forecasts_frozen.json is committed and
# its SHA-256 appears in a commit message (forecasts frozen before any experience run).
R="/Users/ishaanmakkar/Documents/Context for Agents/Tools/trustcurve"; cd "$R"
F=results/study2/forecasts_frozen.json
[[ -f "$F" ]] || { echo "no frozen forecasts"; exit 2; }
H=$(shasum -a 256 "$F" | cut -d' ' -f1)
git log --format=%B | grep -q "$H" || { echo "forecast hash $H not in any commit message: not frozen"; exit 2; }
git diff --quiet HEAD -- "$F" || { echo "frozen forecasts modified since commit"; exit 2; }
E=tasks/study2/experience_main; ORDER=$E/order.txt; DESIGN=results/study2/phaseC_design.json
PY="$HOME/.local/share/trustcurve/.venv/bin/python"
"$PY" - "$DESIGN" "$ORDER" "$E" <<'PYEOF' > results/study2/phaseC_exp_batches.txt
import json, sys
d = json.load(open(sys.argv[1])); order = [l.strip() for l in open(sys.argv[2]) if l.strip()]; E = sys.argv[3]
for c, v in d.items():
    for n, tag in ((v["n_e"], ""), (v.get("bridge_n", 0), "bridge")):
        if not n:
            continue
        ids = f"{E}/ids_{n}.txt"; open(ids, "w").write("\n".join(order[:n]) + "\n")
        sims = [("anthropic/claude-sonnet-5-5", "S"), ("openai/gpt-6-luna", "L")] if not tag else [("anthropic/claude-haiku-5-5", "H")]
        for llm, lab in sims:
            print(f"exp-{c}-{lab} {c} {llm} {lab} {ids}")
PYEOF
rm -f results/study2/STOP_FLAG
run_one() {
  set -- $1
  [[ -f "$R/results/study2/STOP_FLAG" ]] && { echo "skip $1"; return; }
  DATE_HINT=1 CONC=4 "$R/scripts/study2/run_batch.sh" C "$1" "$2" "$R/tasks/study2/experience_main/pool.json" "$R/tasks/study2/experience_main/meta.json" "$3" "$4" "$5" > /dev/null 2>&1
  rc=$?; [[ $rc -eq 3 ]] && touch "$R/results/study2/STOP_FLAG"
  echo "$1 rc=$rc $(tail -1 "$R/results/study2/logs/$1.log")"
}
export -f run_one; export R
cat results/study2/phaseC_exp_batches.txt | xargs -P "${PAR:-5}" -I{} bash -c 'run_one "{}"'
echo PHASEC_EXP_DONE
