#!/usr/bin/env python3
"""Summarise results/ into a markdown report.

    python3 report.py [results-dir] [--include-smoke]   # prints markdown to stdout
"""
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import verify

SAME_ACCURACY = 2.0  # points; smaller differences count as "same accuracy"
TIMER_TOOLS = {"ScheduleWakeup", "CronCreate", "Monitor"}  # run.sh disallows these


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def subagents(transcript: Path) -> list[dict]:
    """One row per subagent run: task, model, effort, seconds, output tokens."""
    rows = []
    for f in sorted(transcript.glob("subagents/agent-*.jsonl")):
        lines = [json.loads(line) for line in f.read_text().split("\n") if line.strip()]
        first_user = next((line for line in lines if line.get("type") == "user"), {})
        m = re.search(r"TASK\s+(\d\d-[\w-]+)", json.dumps(first_user.get("message", {})))
        replies = [line for line in lines if line.get("type") == "assistant"]
        usage = {r.get("requestId"): r["message"].get("usage", {}) for r in replies}  # dedupe per request
        stamps = [ts(line["timestamp"]) for line in lines if line.get("timestamp")]
        rows.append({
            "task": m.group(1) if m else "?",
            "model": replies[0]["message"].get("model", "?") if replies else "?",
            "effort": replies[0].get("effort", "?") if replies else "?",
            "seconds": (max(stamps) - min(stamps)).total_seconds() if stamps else 0.0,
            "output_tokens": sum(u.get("output_tokens", 0) for u in usage.values()),
        })
    return rows


def idle_tail(transcript: Path) -> float:
    """Seconds the boss sat waiting on a ScheduleWakeup timer after all work was done."""
    def stamps(f: Path) -> list[datetime]:
        return sorted(ts(r["timestamp"]) for r in map(json.loads, filter(str.strip, f.read_text().split("\n")))
                      if r.get("timestamp"))
    mains = list(transcript.glob("*.jsonl"))
    work = [t for f in transcript.glob("subagents/agent-*.jsonl") for t in stamps(f)]
    if not mains or not work:
        return 0.0
    after = [t for t in stamps(mains[0]) if t >= max(work)]
    # The final summary is followed by a >2 min silence that ends only when the timer fires.
    end = next((a for a, b in zip(after, after[1:]) if (b - a).total_seconds() > 120), None)
    return (after[-1] - end).total_seconds() if end else 0.0


def timer_calls(transcript: Path) -> list[str]:
    """Names of timer tools the boss called; these can leave claude -p idle until they fire."""
    calls = []
    for f in transcript.glob("*.jsonl"):
        for r in map(json.loads, filter(str.strip, f.read_text().split("\n"))):
            content = r.get("message", {}).get("content") if isinstance(r.get("message"), dict) else None
            calls += [c["name"] for c in content or [] if isinstance(c, dict) and c.get("type") == "tool_use"
                      and c.get("name") in TIMER_TOOLS]
    return calls


def load_runs(results: Path, include_smoke: bool) -> list[dict]:
    runs = []
    for d in sorted(results.iterdir()):
        if not (d / "meta.json").exists() or not (d / "scores.json").exists():
            continue
        meta = json.loads((d / "meta.json").read_text())
        if meta["tasks"] != "*" and not include_smoke:
            continue
        try:
            claude = json.loads((d / "claude.json").read_text())
        except (OSError, json.JSONDecodeError):
            claude = {"is_error": True}
        scores = json.loads((d / "scores.json").read_text())
        subs = subagents(d / "transcript") if (d / "transcript").is_dir() else []
        per_task_seconds = defaultdict(float)
        for s in subs:
            per_task_seconds[s["task"]] += s["seconds"]  # attempts of one task run one after another
        idle = idle_tail(d / "transcript") if (d / "transcript").is_dir() else 0.0
        runs.append({
            "id": d.name, **meta, "claude": claude, "scores": scores, "subagents": subs,
            "wall_seconds": meta["wall_seconds"] - idle, "idle_seconds": idle,
            "timer_calls": timer_calls(d / "transcript"),
            "accuracy": statistics.mean(v["score"] for v in scores.values()) if scores else 0.0,
            "cost": claude.get("total_cost_usd", 0.0),
            "output_tokens": sum(m.get("outputTokens", 0) for m in claude.get("modelUsage", {}).values()),
            "sendbacks": max(0, len(subs) - len({s["task"] for s in subs})),
            "slowest_task": max(per_task_seconds.values(), default=0.0),
        })
    return runs


def spread(values: list[float], fmt: str) -> str:
    if not values:
        return "–"
    mean = statistics.mean(values)
    if len(values) == 1:
        return format(mean, fmt)
    return f"{format(mean, fmt)} ({format(min(values), fmt)}–{format(max(values), fmt)})"


def short(model: str) -> str:
    return model.removeprefix("claude-")


def label(arm: str, runs: list[dict]) -> str:
    cfg = runs[0]["config"]
    return f"{arm.upper()}: {cfg['WORKER_MODEL']} @ {cfg['WORKER_EFFORT']} workers"


def mean_of(runs: list[dict], key: str) -> float:
    return statistics.mean(r[key] for r in runs)


def verdict(a: list[dict], b: list[dict], arm: str) -> str:
    acc = (mean_of(b, "accuracy") - mean_of(a, "accuracy")) * 100
    wall = mean_of(b, "wall_seconds") / mean_of(a, "wall_seconds") - 1
    cost = mean_of(b, "cost") / max(mean_of(a, "cost"), 1e-9) - 1
    X = arm.upper()
    facts = f"accuracy {acc:+.1f} points, wall time {wall:+.0%}, cost {cost:+.0%} ({X} vs A)"
    if acc < -SAME_ACCURACY:
        return f"**{X}: refuted on quality**: the fast workers lost accuracy; {facts}."
    if wall < 0 or cost < 0:
        gains = " and ".join(x for x, ok in [("cheaper", cost < 0), ("faster", wall < 0)] if ok)
        return f"**{X}: supported**: same accuracy (within {SAME_ACCURACY:.0f} points) and {X} was {gains}; {facts}."
    return f"**{X}: refuted on efficiency**: same accuracy, but {X} was neither faster nor cheaper; {facts}."


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    results = Path(args[0]) if args else Path(__file__).parent / "results"
    runs = load_runs(results, "--include-smoke" in sys.argv)
    if not runs:
        sys.exit(f"no finished runs in {results}")
    by_arm = defaultdict(list)
    for r in runs:
        by_arm[r["arm"]].append(r)
    arms = sorted(by_arm)
    names = {a: label(a, by_arm[a]) for a in arms}
    starter = verify.score_workspace(verify.TASKS)
    tasks = sorted({t for r in runs for t in r["scores"]})
    p = print

    cfg = runs[0]["config"]
    p("# Opus brain + fast workers — results\n")
    p(f"Boss in all arms: `{cfg['ORCH_MODEL']}` @ {cfg['ORCH_EFFORT']}. "
      + "; ".join(f"arm {names[a]}" for a in arms) + f". Runs: {', '.join(r['id'] for r in runs)}.\n")

    others = [a for a in arms if a != "a"] if "a" in by_arm else []
    if others:
        p("## Verdict (each arm vs baseline A)\n")
        for x in others:
            p(f"- {verdict(by_arm['a'], by_arm[x], x)} Based on {len(by_arm['a'])} vs {len(by_arm[x])} runs.")
        p("\nCheck the min–max ranges below: if they overlap a lot, the difference may be noise.\n")

    p("## Summary (mean, min–max over runs)\n")
    p("| Arm | Runs | Accuracy | Wall time (min) | Slowest task (min) | Cost, API-equivalent ($) "
      "| Output tokens (k) | Send-backs per run |")
    p("|---|---|---|---|---|---|---|---|")
    for a in arms:
        rs = by_arm[a]
        p(f"| {names[a]} | {len(rs)} | {spread([r['accuracy'] * 100 for r in rs], '.1f')}% "
          f"| {spread([r['wall_seconds'] / 60 for r in rs], '.1f')} "
          f"| {spread([r['slowest_task'] / 60 for r in rs], '.1f')} "
          f"| {spread([r['cost'] for r in rs], '.2f')} "
          f"| {spread([r['output_tokens'] / 1000 for r in rs], '.0f')} "
          f"| {spread([r['sendbacks'] for r in rs], '.1f')} |")
    p("\nWorkers run in parallel, so wall time ≈ slowest task + the boss's own planning and review. "
      "A send-back is the boss rejecting a worker's result and spawning a new attempt.\n")

    p("## Per task (mean over runs)\n")
    p("| Task | Do-nothing score | " + " | ".join(f"{names[a]}: accuracy" for a in arms)
      + " | " + " | ".join(f"{a.upper()}: attempts" for a in arms)
      + " | " + " | ".join(f"{a.upper()}: worker time (s)" for a in arms) + " |")
    p("|---|---|" + "---|" * (3 * len(arms)))
    for t in tasks:
        acc = [spread([r["scores"][t]["score"] * 100 for r in by_arm[a] if t in r["scores"]], ".0f") + "%" for a in arms]
        attempts = [spread([sum(s["task"] == t for s in r["subagents"]) for r in by_arm[a]], ".1f") for a in arms]
        secs = [spread([sum(s["seconds"] for s in r["subagents"] if s["task"] == t) for r in by_arm[a]], ".0f")
                for a in arms]
        p(f"| {t} | {starter.get(t, {}).get('score', 0) * 100:.0f}% | " + " | ".join(acc + attempts + secs) + " |")

    any_lost = False
    for x in others:
        lost = [(t, statistics.mean(r["scores"][t]["score"] for r in by_arm["a"] if t in r["scores"]) -
                 statistics.mean(r["scores"][t]["score"] for r in by_arm[x] if t in r["scores"]))
                for t in tasks if all(any(t in r["scores"] for r in by_arm[y]) for y in ("a", x))]
        lost = [(t, d) for t, d in lost if d > 0.02]
        if lost:
            any_lost = True
            p(f"\nWhere {x.upper()} scored lower than A: " + ", ".join(f"{t} (−{d * 100:.0f} points)" for t, d in lost) + ".")
    if any_lost:
        p("The scorer's detail for each run is in `results/<run>/scores.json`.")

    models = sorted({m for r in runs for m in r["claude"].get("modelUsage", {})})
    p("\n## Cost by model (mean $ per run)\n")
    p("| Arm | " + " | ".join(short(m) for m in models) + " |")
    p("|---|" + "---|" * len(models))
    for a in arms:
        p(f"| {names[a]} | " + " | ".join(
            f"{statistics.mean(r['claude'].get('modelUsage', {}).get(m, {}).get('costUSD', 0) for r in by_arm[a]):.2f}"
            for m in models) + " |")

    problems = []
    for r in runs:
        notes = []
        if r["claude"].get("is_error"):
            notes.append("claude reported an error (check budget cap)")
        if r["claude"].get("permission_denials"):
            notes.append(f"{len(r['claude']['permission_denials'])} blocked shell commands")
        others = set(r["claude"].get("subagent_stats", {}).get("by_type", {})) - {"worker"}
        if others:
            notes.append(f"boss also used non-worker subagents {sorted(others)}")
        if r["idle_seconds"] > 0:
            notes.append(f"{r['idle_seconds'] / 60:.1f} min idle tail after the final answer (subtracted from wall time)")
        if r["timer_calls"]:
            notes.append(f"boss called timer tools {sorted(set(r['timer_calls']))} ({len(r['timer_calls'])}x)")
        if not r["subagents"]:
            notes.append("no transcript, so per-task timing is missing")
        if notes:
            problems.append(f"- {r['id']}: " + "; ".join(notes))
    if problems:
        p("\n## Run problems\n")
        p("\n".join(problems))


if __name__ == "__main__":
    main()
