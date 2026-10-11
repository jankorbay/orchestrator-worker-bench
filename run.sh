#!/usr/bin/env bash
# Run one benchmark arm once.
#   ./run.sh <a|b|c|d|e> <rep> [task-glob]      e.g. ./run.sh b 1   or   ./run.sh a smoke '01-*'
# Writes results/<arm>-<rep>/: claude.json, scores.json, meta.json, transcript/, workspace/
set -euo pipefail
cd "$(dirname "$0")"
set -a; source config.env; set +a

arm=${1:?arm a, b or c}; rep=${2:?rep}; only=${3:-*}
[[ $arm == [abcde] ]] || { echo "arm must be a, b, c, d or e" >&2; exit 1; }
out="results/$arm-$rep"
[[ -e $out ]] && { echo "$out already exists" >&2; exit 1; }
mkdir -p "$out"

# Workspace lives outside the repo so agents cannot find verify/ (hidden tests).
ws=$(mktemp -d "${TMPDIR:-/tmp}/haiku-bench-$arm-$rep.XXXX")
# No trailing slash on the source: BSD cp would copy the folder's contents, not the folder.
for d in tasks/$only; do [[ -d $d ]] && cp -R "$d" "$ws/"; done
ls -d "$ws"/[0-9][0-9]-*/ >/dev/null 2>&1 || { echo "no task folders matched '$only'" >&2; rm -rf "$ws" "$out"; exit 1; }

# Same prompt and same roster in every arm; only the worker's model and effort differ.
case $arm in
  a) WORKER_MODEL=$A_WORKER_MODEL WORKER_EFFORT=$A_WORKER_EFFORT ;;
  b) WORKER_MODEL=$B_WORKER_MODEL WORKER_EFFORT=$B_WORKER_EFFORT ;;
  c) WORKER_MODEL=$C_WORKER_MODEL WORKER_EFFORT=$C_WORKER_EFFORT ;;
  d) WORKER_MODEL=$D_WORKER_MODEL WORKER_EFFORT=$D_WORKER_EFFORT ;;
  e) WORKER_MODEL=$E_WORKER_MODEL WORKER_EFFORT=$E_WORKER_EFFORT ;;
esac
export WORKER_MODEL WORKER_EFFORT
agents=$(python3 -c '
import json, os
e = os.environ
print(json.dumps({"worker": {"description": "Software engineer. Give it exactly one task folder.",
                             "prompt": open("spec/worker.md").read(),
                             "model": e["WORKER_MODEL"], "effort": e["WORKER_EFFORT"]}}))')
prompt=$(cat spec/SPEC.md)

echo "[$arm-$rep] running in $ws"
start=$(python3 -c 'import time; print(time.time())')
(cd "$ws" && claude -p "$prompt" \
  --model "$ORCH_MODEL" --effort "$ORCH_EFFORT" --agents "$agents" \
  --output-format json --max-budget-usd "$MAX_BUDGET_USD" \
  --setting-sources project --strict-mcp-config --disable-slash-commands \
  --permission-mode acceptEdits --allowedTools "$ALLOWED_TOOLS" \
  --disallowedTools ScheduleWakeup,CronCreate,Monitor \
  --settings '{"sandbox":{"enabled":true,"allowUnsandboxedCommands":false,"failIfUnavailable":true}}') > "$out/claude.json" \
  || echo "[$arm-$rep] claude exited non-zero, scoring anyway" >&2
end=$(python3 -c 'import time; print(time.time())')

python3 verify.py "$ws" > "$out/scores.json"
cp -R "$ws" "$out/workspace"

# Keep the session transcripts (per-subagent model, effort, timing) next to the results.
sid=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("session_id",""))' "$out/claude.json" 2>/dev/null || true)
main=$( [[ -n $sid ]] && find ~/.claude/projects -maxdepth 2 -name "$sid.jsonl" | head -1 || true)
if [[ -n $main ]]; then
  mkdir -p "$out/transcript"
  cp "$main" "$out/transcript/"
  [[ -d ${main%.jsonl} ]] && cp -R "${main%.jsonl}/." "$out/transcript/"
else
  echo "[$arm-$rep] transcript not found; per-task timing will be missing" >&2
fi

python3 - "$out" "$arm" "$rep" "$start" "$end" "$only" <<'PY'
import json, os, sys
out, arm, rep, start, end, only = sys.argv[1:]
keys = ["ORCH_MODEL", "ORCH_EFFORT", "WORKER_MODEL", "WORKER_EFFORT", "MAX_BUDGET_USD"]
json.dump({"arm": arm, "rep": rep, "tasks": only, "wall_seconds": round(float(end) - float(start), 1),
           "config": {k: os.environ[k] for k in keys}}, open(f"{out}/meta.json", "w"), indent=2)
PY
rm -rf "$ws"
echo "[$arm-$rep] done: $(python3 -c 'import json,sys; s=json.load(open(sys.argv[1])); print({k: v["score"] for k, v in s.items()})' "$out/scores.json")"
